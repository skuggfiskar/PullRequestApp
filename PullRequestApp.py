import tkinter as tk
from tkinter import ttk
import requests
import json

class PullRequestApp:
    def __init__(self, master):
        self.master = master
        self.master.configure(bg="#f0f0f0")

        self.frame = tk.Frame(self.master, bg="#f0f0f0")
        self.frame.pack(padx=20, pady=0, fill="both", expand=True)

        self.title_label = tk.Label(self.frame, text="Open Pull Requests", font=("Arial", 20, "bold"), bg="#f0f0f0")
        self.title_label.pack(pady=0)

        self.load_config()
        self.load_pat()

        self.pull_requests = self.get_pull_requests()

        self.counter_label = tk.Label(self.frame, text=f"Total Pull Requests: {len(self.pull_requests)}", font=("Arial", 14), bg="#f0f0f0")
        self.counter_label.pack(pady=0)

        self.create_scrollable_list()
        self.display_pull_requests()

    def load_config(self):
        with open("config.json", "r") as file:
            config = json.load(file)
            self.repositories = config["repositories"]

    def load_pat(self):
        with open("secret_pat.txt", "r") as file:
            self.pat = file.readline().strip()

    def get_pull_requests(self):
        pull_requests = []
        base_url = "https://api.github.com/repos/"
        headers = {
            "Authorization": f"token {self.pat}",
            "Accept": "application/vnd.github+json",
        }

        for repo in self.repositories:
            url = f"{base_url}{repo}/pulls"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                pull_requests.extend(response.json())
            else:
                print(f"Error fetching pull requests from {repo}: {response.text}")

        return pull_requests

    def create_scrollable_list(self):
        self.canvas = tk.Canvas(self.frame, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.list_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        # Bind the mouse scroll event to the canvas
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_scroll)
    
    def on_mouse_scroll(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def display_pull_requests(self):
        for pr in self.pull_requests:
            pr_title = pr["title"]
            pr_description = pr["body"]
            pr_url = pr["html_url"]

            pr_label = tk.Label(self.list_frame, text=pr_title, font=("Arial", 14), fg="#0366d6", cursor="hand2", bg="#f0f0f0")
            pr_label.pack(pady=(10, 0), fill="x")  # Fill horizontally
            pr_label.bind("<Button-1>", lambda event, url=pr_url: self.open_pull_request(url))

            desc_text = tk.Text(self.list_frame, wrap="word", height=5, bg="#f0f0f0", bd=0, padx=4)
            if pr_description:
                desc_text.insert(tk.END, pr_description)
            else:
                desc_text.insert(tk.END, "No description provided.")
            desc_text.config(state="disabled")
            desc_text.pack(pady=(5, 10), padx=10, ipady=5, anchor="w", fill="both", expand=True)

            separator = ttk.Separator(self.list_frame, orient="horizontal")
            separator.pack(fill="x", pady=(0, 10))

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
    root.geometry("1200x1000")
    app = PullRequestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
