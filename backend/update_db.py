from sqlalchemy import create_engine, text
from model import Base

# Database connection
DATABASE_URL = "postgresql://blasey:0308@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)

# Update the password_hash column length
with engine.connect() as connection:
    connection.execute(text("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(512)"))
    connection.commit()

print("Database schema updated successfully!") 