from ai_engine import understand_question


columns = [
    "Order_ID",
    "Order_Date",
    "Customer",
    "Country",
    "Category",
    "Product",
    "Quantity",
    "Sales",
    "Profit",
    "Payment_Method"
]


numeric_columns = [
    "Quantity",
    "Sales",
    "Profit"
]


categorical_columns = [
    "Order_ID",
    "Order_Date",
    "Customer",
    "Country",
    "Category",
    "Product",
    "Payment_Method"
]


question = "Show sales trend over time"


try:

    result = understand_question(
        question,
        columns,
        numeric_columns,
        categorical_columns
    )

    print("\nAI Analysis Plan:")
    print(result)


except Exception as e:

    print("\nError:")
    print(e)