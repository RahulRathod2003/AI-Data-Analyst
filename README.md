\# 🤖 AI Data Analyst – Natural Language Data Analysis Platform



An AI-powered data analysis platform that allows users to upload CSV datasets and interact with their data using natural language.



Instead of writing Python or SQL queries manually, users can ask questions such as:



\- "What is the total sales?"

\- "What are the top 5 products by sales?"

\- "Show sales by country."

\- "Which month had the highest sales?"

\- "What is the relationship between sales and profit?"



The platform converts natural-language questions into structured analysis plans, performs real calculations using Pandas, generates interactive Plotly visualizations, and provides AI-powered business insights.



\---



\## 🚀 Key Features



\### 📊 Executive Dashboard

\- Dataset KPIs

\- Row and column statistics

\- Numeric and categorical column overview

\- Business-oriented dashboard experience



\### 📁 Multi-File Data Analysis

\- Upload multiple CSV files

\- Automatically combine datasets

\- Track source files

\- Analyze larger datasets



\### 🤖 Natural Language Data Analysis

Ask questions about your data using normal language.



Example:



> What are the total sales by country?



The AI converts the question into a structured analysis plan before computation.



\### 🧠 AI Analysis Planner



The AI identifies:



\- Analysis operation

\- Numeric column

\- Grouping column

\- Aggregation method

\- Date column

\- Time granularity



The structured plan is then executed using Pandas.



\### 🐼 Pandas Analysis Engine



Actual numerical calculations are performed using Pandas rather than allowing the LLM to invent numerical results.



Supported analysis includes:



\- Total

\- Average

\- Minimum

\- Maximum

\- Count

\- Unique count

\- Group-by analysis

\- Top N

\- Bottom N

\- Correlation

\- Date trends



\### 📈 Interactive Visualizations



Plotly is used to generate interactive charts for analytical results.



Charts can include:



\- Bar charts

\- Line charts

\- Scatter plots

\- Histograms

\- Correlation visualizations

\- Time-series charts



\### 💡 AI Business Insights



After computation, the AI generates concise business-oriented explanations based on the calculated results.



The AI is instructed to:



\- Use only available analysis results

\- Avoid inventing causes

\- Avoid unsupported assumptions

\- Highlight important differences

\- Provide recommendations separately when appropriate



\### 🔎 Smart Filters



Users can filter datasets using available fields and date ranges before performing analysis.



\### 🧹 Data Quality Assistant



Automatically identifies common data-quality issues such as:



\- Missing values

\- Duplicate records

\- Data types

\- Unique values

\- Potential quality problems



\### 🛠️ Data Cleaning Assistant



Provides data-cleaning functionality for preparing datasets before analysis.



\### 📊 Automated EDA



Automatically explores the uploaded dataset and surfaces:



\- Dataset structure

\- Numeric columns

\- Categorical columns

\- Distributions

\- Correlations

\- Important patterns



\### 📈 Advanced Analytics



Provides additional analytical capabilities for deeper exploration of the dataset.



\### 💬 Conversational AI



Users can continue asking follow-up questions about their dataset instead of starting every analysis from scratch.



\### 📄 Professional Reports



Generate professional PDF analysis reports containing analytical results and insights.



\### 🐳 Docker Support



The application includes Docker configuration for containerized execution.



Docker support includes:



\- Python 3.11 environment

\- Dependency installation

\- Non-root application user

\- Container health check

\- Docker Compose configuration



\---



\# 🏗️ System Architecture



```text

&#x20;                   ┌─────────────────────┐

&#x20;                   │        User         │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │    CSV Upload       │

&#x20;                   │   Multiple Files    │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │   Data Quality      │

&#x20;                   │   \& Cleaning        │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │   Smart Filters     │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │ Natural Language    │

&#x20;                   │     Question        │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │    Groq LLM         │

&#x20;                   │  Question Planner   │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │ Structured Analysis │

&#x20;                   │       Plan          │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │ Pandas Analysis     │

&#x20;                   │      Engine         │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │ Plotly Visualization│

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │   AI Business       │

&#x20;                   │      Insights       │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

&#x20;                   ┌─────────────────────┐

&#x20;                   │   PDF Report        │

&#x20;                   └─────────────────────┘

