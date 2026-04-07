# Goldwins - Microgrid Panel Generator

A powerful Streamlit-based web application for generating professional Single Line Diagrams (SLDs) for microgrids. Create, visualize, and export detailed electrical system diagrams with an intuitive interface and modern design.

## Features

- 🎨 **Interactive Diagram Builder** - Drag-and-drop interface for creating microgrid system diagrams
- 📊 **Professional Visualization** - Generate clear, professional Single Line Diagrams (SLDs)
- 📄 **PDF Export** - Export diagrams as high-quality PDF documents
- 🎭 **Modern UI** - Premium dark theme with responsive design
- ⚡ **Real-time Preview** - Instant preview of diagram changes

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JyotsnaGuntha/Goldwins.git
cd Goldwins
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Project Structure

```
Goldwins/
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Dependencies

- **streamlit** - Web application framework
- **svgwrite** - SVG generation and manipulation
- **reportlab** - PDF document generation
- **cairosvg** - SVG to image conversion

## Usage

1. Launch the application using the command above
2. Configure your microgrid parameters in the sidebar
3. Define system components (generators, loads, transformers, etc.)
4. Preview your SLD in real-time
5. Export as PDF for documentation and sharing

## Technology Stack

- **Frontend**: Streamlit
- **Graphics**: SVG (svgwrite)
- **Document Generation**: ReportLab
- **Language**: Python 3.x

## File Format Support

- **Output**: PDF, SVG

## Contributing

Contributions are welcome! Feel free to:
- Fork the repository
- Create feature branches
- Submit pull requests
- Report issues

## License

This project is open source and available under the MIT License.

## Author

**Jyotsna Guntha**
- GitHub: [@JyotsnaGuntha](https://github.com/JyotsnaGuntha)

## Support

For issues, questions, or suggestions, please open an issue on [GitHub Issues](https://github.com/JyotsnaGuntha/Goldwins/issues).
