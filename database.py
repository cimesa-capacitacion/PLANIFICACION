import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Si existe la variable de entorno DATABASE_URL (en Render), la usamos.
# Si no, usamos SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanban.db")

# Render a veces proporciona URLs de PostgreSQL que empiezan con 'postgres://'
# pero SQLAlchemy requiere que empiecen con 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Configuración para PostgreSQL
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
