# Dabba - AI-Powered Expense Tracker with Chatbot

A comprehensive expense tracking application with an AI-powered chatbot that provides personalized financial advice based on your spending data.

## Features

### 📊 Dashboard
- Real-time financial overview
- Income vs expense tracking
- Category-wise spending analysis
- Payment method insights
- Transaction history

### 📈 Advanced Analytics
- Daily spending patterns
- Monthly trends analysis
- Category spending heatmaps
- Payment method analysis
- Weekly spending patterns
- Savings rate tracking

### 🤖 AI Chatbot
- Personalized financial advice
- Spending pattern analysis
- Savings recommendations
- Budget optimization tips
- Transaction insights
- Financial goal suggestions

## Setup Instructions

### 1. Database Setup
1. Install XAMPP and start Apache and MySQL services
2. Create a database named `dabba`
3. Import the `dabba.sql` file into your MySQL database
4. Ensure the database is running on `localhost:3306`

### 2. Python Environment
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Grok AI API Setup
1. Sign up for a Grok AI API key at [Groq](https://console.groq.com/)
2. Update the API key in `.streamlit/secrets.toml`:
   ```toml
   GROK_API_KEY = "your-actual-grok-api-key-here"
   ```

### 4. Run the Application
```bash
streamlit run app.py
```

## Demo Accounts

You can use any of these accounts to test the application:

| Email | Password |
|-------|----------|
| himnish@gmail.com | himnish@123 |
| rishi@gmail.com | rishi@123 |
| surya@gmail.com | surya@123 |
| sandeep@gmail.com | sandeep@123 |
| shaura@gmail.com | shaura@123 |

## Chatbot Features

### 🤖 AI-Powered Financial Advisor
The chatbot uses Grok AI to provide personalized financial insights based on your transaction data:

- **Spending Analysis**: Get insights on your spending patterns and categories
- **Savings Advice**: Receive personalized recommendations to improve your savings
- **Budget Optimization**: Get tips on how to better manage your finances
- **Trend Analysis**: Understand your financial trends over time
- **Goal Setting**: Get advice on setting and achieving financial goals

### 💬 Sample Questions
- "What are my biggest spending categories?"
- "How can I improve my savings?"
- "What's my spending trend over the last few months?"
- "Which payment method do I use most?"
- "What are my recent transactions?"
- "How does my income compare to my expenses?"
- "What financial advice do you have for me?"
- "How can I reduce my expenses?"

## Database Schema

### Users Table
- `user_id`: Primary key
- `Name`: User's full name
- `Age`: User's age
- `email`: User's email address
- `password`: User's password
- `phone_number`: User's phone number

### Data Table
- `id`: Foreign key to Users table
- `Date`: Transaction date
- `Mode`: Payment method (UPI, Cash, etc.)
- `Category`: Expense category
- `Amount`: Transaction amount
- `income_expense`: Type of transaction (Income/Expense)
- `Currency`: Currency code (INR)

## Security Features

- **User Authentication**: Secure login system
- **Data Privacy**: Each user can only access their own data
- **API Security**: Secure API key management
- **Session Management**: Secure session handling

## Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MySQL (XAMPP)
- **AI**: Grok AI API
- **Visualization**: Plotly
- **Data Processing**: Pandas

## Troubleshooting

### Database Connection Issues
- Ensure XAMPP is running
- Check if MySQL service is started
- Verify database name is `dabba`
- Confirm port 3306 is available

### API Issues
- Verify your Grok API key is correct
- Check internet connection
- Ensure API key has sufficient credits

### Application Issues
- Restart the Streamlit application
- Clear browser cache
- Check Python dependencies are installed correctly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository. 