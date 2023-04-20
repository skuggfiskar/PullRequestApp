import threading
import tkinter as tk
from tkinter import ttk
import tkinter.font
import requests
import json5
import datetime

class PullRequestApp:
    DESCRIPTION_ROWS = 2
    def __init__(self, master):
        self.master = master
        self.master.configure(bg="#f0f0f0")

        self.frame = tk.Frame(self.master, bg="#f0f0f0")
        self.frame.pack(padx=20, pady=0, fill="both", expand=True)

        self.font_title = tk.font.Font(family="Arial", size=12, weight="bold")
        self.font_desc = tk.font.Font(family="Arial", size=10)

        self.title_label = tk.Label(self.frame, text="Open Pull Requests", font=("Arial", 14, "bold"), bg="#f0f0f0")
        self.title_label.pack(pady=0)

        self.load_config()
        self.load_pat()

        self.counter_label = tk.Label(self.frame, text="Total Pull Requests: ...", font=("Arial", 10), bg="#f0f0f0")
        self.counter_label.pack(pady=0)

        self.refresh_button = tk.Button(self.frame, text="Refresh", command=self.refresh_list, state="disabled")
        self.refresh_button.pack(padx=(10, 0))

        self.create_scrollable_list()

        # Load the pull requests list in the background
        self.load_pull_requests()

        self.refresh_job = None
        self.refresh_interval = self.refresh_interval
        self.load_pull_requests()

    def load_config(self):
        with open("config.json", "r") as file:
            config = json5.load(file)
            self.repositories = config["repositories"]
            self.DESCRIPTION_ROWS = config["UI"]["description"]["rows-visible"]
            self.filter_not_reviewed_by_me = config["show-only-not-reviewed-by-me"]
            self.refresh_interval = config["seconds-between-automatic-refresh"]

    def load_pat(self):
        with open("secret_pat.txt", "r") as file:
            self.pat = file.readline().strip()

    def load_pull_requests(self):
        # Disable the refresh button during loading
        self.refresh_button.config(state="disabled")
        self.counter_label.config(text="Loading...")

        # Use a separate thread to load the pull requests
        load_thread = threading.Thread(target=self.fetch_pull_requests)
        load_thread.start()
    
    def fetch_pull_requests(self):
        self.pull_requests = self.get_pull_requests()

        # Update the UI after loading
        self.master.after(0, self.update_list)

        # Schedule the next refresh after loading
        self.schedule_refresh()

    def schedule_refresh(self):
        if self.refresh_job:
            # Cancel the previous refresh job
            self.master.after_cancel(self.refresh_job)
        self.refresh_job = self.master.after(self.refresh_interval * 1000, self.refresh_list)

    def clear_list(self):
        # Remove all children of list_frame
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def update_list(self):
        self.clear_list()  # Clear the existing list
        self.display_pull_requests()

        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M")
        self.counter_label.config(text=f"Total Pull Requests: {len(self.pull_requests)} | Last refresh: {timestamp}")

        # Enable the refresh button after loading
        self.refresh_button.config(state="normal")

    def refresh_list(self):
        # Disable the refresh button during loading
        self.refresh_button.config(state="disabled")
        self.counter_label.config(text="Refreshing...")

        # Use a separate thread to load the pull requests
        load_thread = threading.Thread(target=self.fetch_pull_requests)
        load_thread.start()

    def get_pull_requests(self):
        pull_requests = []
        base_url = "https://api.github.com/repos/"
        headers = {
            "Authorization": f"token {self.pat}",
            "Accept": "application/vnd.github+json",
        }

        # Get the user login
        if self.filter_not_reviewed_by_me:
            user_response = requests.get("https://api.github.com/user", headers=headers)
            user_login = user_response.json()["login"]

        for repo in self.repositories:
            url = f"{base_url}{repo}/pulls"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                prs = response.json()
                filtered_pull_requests = []
                for pr in prs:
                    pr['repo_name'] = repo.split('/')[-1]
                    pr['author'] = pr['user']['login']

                    reviews_url = pr['url'] + "/reviews"
                    reviews_response = requests.get(reviews_url, headers=headers)
                    if reviews_response.status_code == 200:
                        reviews = reviews_response.json()
                        approvals = [r for r in reviews if r['state'] == 'APPROVED']
                        pr['num_approvals'] = len(approvals)

                        # Check if the user has already reviewed the PR
                        if self.filter_not_reviewed_by_me:
                            # TODO: check the approved state
                            already_reviewed = any(review["user"]["login"] == user_login for review in reviews)

                            if not already_reviewed:
                                filtered_pull_requests.append(pr)
                        else:
                            filtered_pull_requests.append(pr)

                pull_requests.extend(filtered_pull_requests)
            else:
                print(f"Error fetching pull requests from {repo}: {response.text}")

        return pull_requests

    def create_scrollable_list(self):
        self.max_text_width = 0

        self.canvas = tk.Canvas(self.frame, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar_y = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.frame, orient="horizontal", command=self.canvas.xview)

        self.list_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        # Update this part to make the scrollbars visible only when needed
        self.list_frame.bind("<Configure>", lambda event: self.update_scrollbars())
        self.canvas.bind("<Configure>", lambda event: self.update_scrollbars())

        # Bind the mouse scroll event to the canvas
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_scroll)

    def update_scrollbars(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        list_frame_height = self.list_frame.winfo_reqheight()

        if list_frame_height > canvas_height:
            self.scrollbar_y.pack(side="right", fill="y")
        else:
            self.scrollbar_y.pack_forget()

        if self.max_text_width > canvas_width:
            self.scrollbar_x.pack(side="bottom", fill="x")
        else:
            self.scrollbar_x.pack_forget()

    def on_mouse_scroll(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def display_pull_requests(self):
        for pr in self.pull_requests:
            pr_title = pr["title"]
            pr_description = pr["body"] or ""  # Handle None values for pr_description
            pr_url = pr["html_url"]
            author = pr["author"]
            num_approvals = pr["num_approvals"]
            repo_name = pr["repo_name"]

            pr_info = f"Author: {author} | Approvals: {num_approvals} | Repo: {repo_name}"

            # Update the max_text_width if necessary
            text_width = max(self.font_title.measure(pr_title), self.font_desc.measure(pr_description))
            if text_width > self.max_text_width:
                self.max_text_width = text_width

            pr_label = tk.Label(self.list_frame, text=pr_title, font=("Arial", 14), fg="#0366d6", cursor="hand2", bg="#f0f0f0", anchor="w")
            pr_label.pack(pady=(0, 0), fill="x")  # Fill horizontally
            pr_label.bind("<Button-1>", lambda event, url=pr_url: self.open_pull_request(url))

            desc_text = tk.Text(self.list_frame, wrap="word", height=self.DESCRIPTION_ROWS, bg="#f0f0f0", bd=0, padx=4)
            if pr_description:
                desc_text.insert(tk.END, f"{pr_info}\n{pr_description}")
            else:
                desc_text.insert(tk.END, f"{pr_info}\nNo description provided.")
            desc_text.config(state="disabled")
            desc_text.pack(pady=(0, 0), padx=0, ipady=0, anchor="w", fill="both", expand=True)

            separator = ttk.Separator(self.list_frame, orient="horizontal")
            separator.pack(fill="x", pady=(0, 0))

        # Bind the <Configure> event of the canvas to adjust the wraplength of desc_label
        self.canvas.bind("<Configure>", self.adjust_wraplength)

        # Bind the <Configure> event of the canvas to adjust the wraplength of desc_label
        self.canvas.bind("<Configure>", self.adjust_wraplength)

    def adjust_wraplength(self, event):
        for widget in self.list_frame.winfo_children():
            if isinstance(widget, tk.Text):
                widget.config(width=self.canvas.winfo_width() // 8)

    def open_pull_request(self, url):
        import webbrowser
        webbrowser.open(url)

def main():
    root = tk.Tk()
    root.title("GitHub Pull Requests")
    root.geometry("800x600")
    app = PullRequestApp(root)
    root.bind("<Configure>", lambda event: app.update_scrollbars())  # Add this line
    root.mainloop()

if __name__ == "__main__":
    main()
