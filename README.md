# **Buildeck \- Magic: The Gathering Deck Builder Assistant**

**Buildeck** is a desktop application designed for Magic: The Gathering players and deck builders. It streamlines the process of converting raw card lists into detailed CSV files, complete with mana costs, types, and descriptions, leveraging the power of the [Scryfall API](https://scryfall.com/docs/api).

## **🚀 Features**

* **Multi-Language Support:** Accurate card data retrieval in **English** and **Spanish**.  
* **Smart Parsing:** Handles quantities (e.g., "4x Lightning Bolt") and complex card names automatically.  
* **Offline Database:** Download the Scryfall "Oracle Cards" database for **instant** searches without API latency.  
* **Advanced Caching:** Local caching system to minimize network requests and respect API rate limits.  
* **Complex Card Support:** Full support for Split cards, Flip cards, and Modal Double-Faced Cards (MDFCs).  
* **Export to CSV:** Generates formatted CSV files compatible with Excel, Google Sheets, and deck-building websites.  
* **Clean Architecture:** Built with a modular, maintainable code structure using Dependency Injection and Repository Pattern.

## **🛠️ Technology Stack**

* **Language:** Python 3.11+  
* **GUI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Modern UI)  
* **Data Source:** Scryfall API  
* **Packaging:** PyInstaller (for standalone executables)

## **📦 Installation & Setup**

### **Prerequisites**

* Python 3.10 or higher  
* Git

### **Steps**

1. **Clone the repository:**  
   git clone \[https://github.com/your-username/buildeck.git\](https://github.com/your-username/buildeck.git)  
   cd buildeck

2. **Create a virtual environment:**  
   python \-m venv .venv  
   source .venv/bin/activate  \# On Windows: .venv\\Scripts\\activate

3. **Install dependencies:**  
   pip install \-r requirements.txt

4. **Run the application:**  
   python main.py

## **🏗️ Building the Executable**

To create a standalone binary for your OS (Windows .exe or macOS App):

python build.py

The output file will be located in the dist/ folder.

## 🗺️ **Roadmap & Future Features**

* [ ] **Card Image Preview:** Display card art when hovering over names.
* [ ] **Deck Analytics:** Visual charts for mana curve and color distribution.
* [ ] **Price Check:** Integration with cardmarket/TCGPlayer pricing.
* [ ] **Import/Export:** Support for Arena/MTGO formats.

## **🤝 Contributing**

Contributions are welcome\! Please fork the repository and create a Pull Request for any features or bug fixes.

1. Fork the Project  
2. Create your Feature Branch (git checkout \-b feature/AmazingFeature)  
3. Commit your Changes (git commit \-m 'Add some AmazingFeature')  
4. Push to the Branch (git push origin feature/AmazingFeature)  
5. Open a Pull Request

## **📄 License**

Distributed under the MIT License. See LICENSE for more information.

*Disclaimer: Buildeck is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.*