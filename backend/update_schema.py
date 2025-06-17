from sqlalchemy import create_engine, text
from model import Base

# Database connection
DATABASE_URL = "postgresql://blasey:0308@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

def update_schema():
    # Update the password_hash column length
    with engine.connect() as connection:
        try:
            connection.execute(text("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(512)"))
            connection.commit()
            print("Successfully updated password_hash column to VARCHAR(512)")
        except Exception as e:
            print(f"Error updating schema: {e}")
            connection.rollback()

if __name__ == "__main__":
    update_schema() 