# Company Analyzer

A Python application that uses CrewAI to analyze companies and provide financial insights using AI agents.

## Features

- **Financial Analysis Agent**: Analyzes company financial performance and market trends
- **Web Search Agent**: Gathers real-time information from the web
- **Research Agent**: Conducts comprehensive research on companies
- **Report Agent**: Generates detailed analysis reports

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Serper API key (for web search functionality)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd company-analyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows:**
   ```bash
   venv\Scripts\Activate.ps1
   ```
   - **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the root directory with your API keys:
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Serper API Configuration (for web search)
SERPER_API_KEY=your_serper_api_key_here
```

## Usage

Run the main application:
```bash
python main.py
```

## Project Structure

```
company-analyzer/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (not in git)
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── agents/
    └── agents/
        ├── financial_analysis_agent.py
        ├── financial_research_agent.py
        ├── report_agent.py
        └── web_search_agent.py
```

## Configuration

The application uses the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI model access
- `SERPER_API_KEY`: Your Serper API key for web search functionality

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [CrewAI](https://github.com/joaomdmoura/crewAI)
- Powered by OpenAI's GPT models
- Web search functionality provided by Serper API 