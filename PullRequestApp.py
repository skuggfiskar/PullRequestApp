import tkinter as tk
import requests
import json

class PullRequestApp:
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)
        self.frame.pack()

        self.title_label = tk.Label(self.frame, text="Open Pull Requests", font=("Arial", 16))
        self.title_label.pack(pady=10)

        self.load_config()
        self.load_pat()
        
        self.pull_requests = self.get_pull_requests()
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


    def display_pull_requests(self):
        for pr in self.pull_requests:
            pr_title = pr["title"]
            pr_description = pr["body"]
            pr_url = pr["html_url"]

            pr_label = tk.Label(self.frame, text=pr_title, font=("Arial", 12), fg="blue", cursor="hand2")
            pr_label.pack()
            pr_label.bind("<Button-1>", lambda event, url=pr_url: self.open_pull_request(url))

            desc_label = tk.Label(self.frame, text=pr_description, wraplength=500, justify="left")
            desc_label.pack(pady=5)

    def open_pull_request(self, url):
        import webbrowser
        webbrowser.open(url)

def main():
    root = tk.Tk()
    root.title("GitHub Pull Requests")
    root.geometry("600x400")
    app = PullRequestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
