import pandas as pd
from sqlalchemy import create_engine, text


# Path to the CSV dataset
csv_file = "data/food_prices.csv"

# PostgreSQL database connection
database_url = (
    "postgresql+psycopg2://"
    "postgres:postgres@postgres:5432/assessment_db"
)


def main():

    # Create a connection to PostgreSQL
    database = create_engine(database_url)

    # Read the CSV file
    print("Reading dataset...")
    data = pd.read_csv(csv_file)

    # Show the size of the dataset
    print(f"Rows found: {len(data)}")
    print(f"Columns found: {len(data.columns)}")

    # Convert the date column to a proper date format
    # Invalid dates will become empty values
    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    # List of columns that should contain numbers
    number_columns = [
        "market_id",
        "latitude",
        "longitude",
        "price",
        "commodity_id",
        "usdprice"
    ]

    # Convert the selected columns to numbers
    # Invalid values will become empty values
    for column in number_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Count invalid dates and prices
    invalid_date_count = data["date"].isna().sum()
    invalid_price_count = data["price"].isna().sum()

    # Remember the number of rows before cleaning
    original_row_count = len(data)

    # Remove rows missing important information
    data = data.dropna(
        subset=[
            "countryiso3",
            "date",
            "price",
            "market_id",
            "market",
            "commodity_id",
            "commodity",
            "unit",
            "currency",
            "category"
        ]
    )

    # Calculate how many rows were removed
    skipped_row_count = original_row_count - len(data)

    # Count the clean rows that will be loaded
    clean_row_count = len(data)

    # Display the cleaning summary
    print("\nLOAD SUMMARY")
    print("------------")
    print(f"Rows read: {original_row_count}")
    print(f"Rows inserted: {clean_row_count}")
    print(f"Rows skipped: {skipped_row_count}")

    print("Skip reasons:")
    print(f"  Invalid dates: {invalid_date_count}")
    print(f"  Invalid prices: {invalid_price_count}")

    # SQL command for creating the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS food_prices (
        id SERIAL PRIMARY KEY,
        countryiso3 VARCHAR(3) NOT NULL,
        date DATE NOT NULL,
        admin1 VARCHAR(255),
        admin2 VARCHAR(255),
        market VARCHAR(255) NOT NULL,
        market_id INTEGER NOT NULL,
        latitude NUMERIC(9,6),
        longitude NUMERIC(9,6),
        category VARCHAR(255) NOT NULL,
        commodity VARCHAR(255) NOT NULL,
        commodity_id INTEGER NOT NULL,
        unit VARCHAR(100) NOT NULL,
        priceflag VARCHAR(50),
        pricetype VARCHAR(50),
        currency VARCHAR(10) NOT NULL,
        price NUMERIC(18,4) NOT NULL,
        usdprice NUMERIC(18,4)
    )
    """

    # Create a fresh table in PostgreSQL
    print("\nConnecting to PostgreSQL...")

    with database.begin() as connection:

        # Remove the old table if it exists
        connection.execute(
            text("DROP TABLE IF EXISTS food_prices")
        )

        # Create the new table
        connection.execute(
            text(create_table_sql)
        )

    print("Table 'food_prices' created successfully.")

    # Load the cleaned data into PostgreSQL
    print("Loading data into PostgreSQL...")

    data.to_sql(
        "food_prices",
        database,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi"
    )

    print("Data loaded successfully.")

    # Create indexes to make searches faster
    print("Creating indexes...")

    with database.begin() as connection:

        # Index for faster country searches
        connection.execute(
            text(  "CREATE INDEX idx_countryiso3 "
                "ON food_prices (countryiso3)"
            )
        )

        # Index for faster date searches
        connection.execute(
            text(
                "CREATE INDEX idx_date "
                "ON food_prices (date)"
            )
        )

        # Index for faster commodity searches
        connection.execute(
            text(
                "CREATE INDEX idx_commodity_id "
                "ON food_prices (commodity_id)"
            )
        )

    print("Indexes created successfully.")

    # Check how many rows are in the database
    with database.connect() as connection:

        result = connection.execute(
            text("SELECT COUNT(*) FROM food_prices")
        )

        database_row_count = result.scalar()

    print(f"Rows in database: {database_row_count}")


# Run the program
if __name__ == "__main__":
    main()