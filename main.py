import tkinter as tk
from tkinter import ttk
import webbrowser
import pickle

from scapers import Century21Scraper, CityaScraper

class OfferApp:
    def __init__(self, root):
        self.root = root
        # Load saved data from file if available
        new, rejected = self.load_data()

        scrapers = [
            CityaScraper("Citya", "https://www.citya.com/annonces/location/appartement,maison/paris-75?sort=b.dateMandat&direction=desc&prixMax=1300&surfaceMin=20"),
            Century21Scraper("Century 21", "https://www.century21.fr/annonces/f/location-maison-appartement/v-paris/s-0-/st-0-/b-0-1300/")
        ]

        source_error = []
        self.new_offers = {}
        self.rejected_offers = {}
        for scraper in scrapers:
            scrap_dict = {}
            try:
                scraper.add_offers(scrap_dict)
            except FileNotFoundError:
                pass
                source_error.append((scraper.get_source_name(), scraper.get_link()))
            
            for url, info in scrap_dict.items():
                if url in new:
                    self.new_offers[url] = new[url]
                    del new[url]
                elif url in rejected:
                    self.rejected_offers[url] = rejected[url]
                else:
                    self.new_offers[url] = info + [False, "☐", "☐", "☐", "☐", "☐"]
        
        self.update_scraper_window = self.update_scraper_warning(source_error) if source_error else None

        new = [(info[0], info[1]) for info in new.values() if info[2]]
        self.removed_offer_window = self.removed_offer_warning(new) if new else None

        self.construct()
        # Save data when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_scraper_warning(self, source_error):
        alert_window = tk.Toplevel(self.root)
        alert_window.title("Warning")
        label = tk.Label(alert_window, text="Some scrapers need to be updated:\n", padx=20, pady=20, justify="left")
        label.pack()
        for name, url in source_error:
            link_label = tk.Label(alert_window, text=name, fg="blue", cursor="hand2")
            link_label.pack()
            link_label.bind("<Button-1>", lambda event, u=url: webbrowser.open(u))
        alert_window.mainloop()
        return alert_window

    def removed_offer_warning(self, removed_offers):
        alert_window = tk.Toplevel(self.root)
        alert_window.title("Warning")
        text = "Some interesting offers were removed:\n"
        for source, name in removed_offers:
            text += f"- {source} : {name}"
        label = tk.Label(alert_window, text=text, padx=20, pady=20, justify="left")
        label.pack()
        alert_window.mainloop()
        return alert_window

    def construct(self):
        self.columns_new = ["Source", "Offer", "Interesting", "Too Far", "Too Expensive", "Poor Heating", "Lack of Furniture", "Sold"]
        self.offer_source_i, self.offer_name_i, self.offer_interest_i = 0, 1, 2
        self.columns_rejected = ["Source", "Offer", "Reason"]
        
        self.tab_control = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab1, text="Offers")
        self.tab_control.add(self.tab2, text="Rejected Offers")

        self.new_tree = self.create_table_new()
        self.rejected_tree = self.create_table_rejected()

        self.tab_control.pack(expand=1, fill="both")

    def create_table_new(self):
        tree = ttk.Treeview(self.tab1, columns=self.columns_new, show="headings")
        for col in self.columns_new:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.column(self.columns_new[self.offer_source_i], width=140)
        tree.column(self.columns_new[self.offer_name_i], width=500)
        urls = list(self.new_offers.keys())
        for url in urls:
            info = self.new_offers[url]
            interesting = self.get_interest_str(info[self.offer_interest_i])        
            tag = ("colored",) if info[self.offer_interest_i] else ()
            tree.insert("", "end", tags=tag, values=[info[0], info[1], interesting, "☐", "☐", "☐", "☐", "☐"])
        tree.tag_configure("colored", background="light green")
        tree.bind("<Button-1>", lambda event: self.on_cell_click_new(event, tree))
        tree.pack()

        return tree

    def get_interest_str(self, interesting: bool):
        return "☒" if interesting else "☐"

    def on_cell_click_new(self, event, tree):
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            tree_row_index = tree.identify_row(event.y)
            row_index = tree.index(tree_row_index)
            url = list(self.new_offers.keys())[row_index]
            column = int(tree.identify_column(event.x)[1:]) - 1
            if column == self.offer_source_i or column == self.offer_name_i:
                webbrowser.open(url) # Open URL
            elif column == self.offer_interest_i:
                interesting = not self.new_offers[url][self.offer_interest_i]
                self.new_offers[url][self.offer_interest_i] = interesting
                tag = ("colored",) if interesting else ()
                value = list(tree.item(tree_row_index, "values"))
                value[2] = self.get_interest_str(interesting)
                tree.item(tree_row_index, tags=tag, values=value)
                tree.tag_configure("colored", background="light green")
            elif column > self.offer_interest_i:
                info = self.new_offers[url]
                self.rejected_offers[url] = [info[0], info[1], self.columns_new[column]]
                self.rejected_tree.insert("", "end", values=self.rejected_offers[url])
                del self.new_offers[url]
                tree.delete(tree_row_index)

    def create_table_rejected(self):
        tree = ttk.Treeview(self.tab2, columns=self.columns_rejected, show="headings")
        for col in self.columns_rejected:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.column(self.columns_new[self.offer_source_i], width=140)
        tree.column(self.columns_new[self.offer_name_i], width=500)
        for _, info in self.rejected_offers.items():
            tree.insert("", "end", values=info)
        tree.bind("<Button-1>", lambda event: self.on_cell_click_rejected(event, tree))
        tree.pack()

        return tree

    def on_cell_click_rejected(self, event, tree):
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            tree_row_index = tree.identify_row(event.y)
            row_index = tree.index(tree_row_index)
            url = list(self.rejected_offers.keys())[row_index]
            column = int(tree.identify_column(event.x)[1:]) - 1
            if column == 2:
                info = self.rejected_offers[url]
                self.new_offers[url] = [info[0], info[1], False]
                self.new_tree.insert("", "end", values=[info[0], info[1], "☐", "☐", "☐", "☐", "☐", "☐"])
                del self.rejected_offers[url]
                tree.delete(tree_row_index)
            else :
                webbrowser.open(url) # Open URL

    def load_data(self):
        new, rejected = {}, {}
        try:
            with open("data.pkl", "rb") as file:
                new, rejected = pickle.load(file)
        except FileNotFoundError:
            pass
        return new, rejected

    def save_data(self):
        with open("data.pkl", "wb") as file:
            pickle.dump((self.new_offers, self.rejected_offers), file)

    def on_closing(self):
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    if True: # Put False to test scrapers.
        root = tk.Tk()
        root.title("Offer Manager")
        app = OfferApp(root)
        root.mainloop()
    else:
        scrap = Century21Scraper("Century 21", "https://www.century21.fr/annonces/f/location-maison-appartement/v-paris/s-0-/st-0-/b-0-1300/")
        dicti = {}
        scrap.add_offers(dicti)
        print(dicti)
