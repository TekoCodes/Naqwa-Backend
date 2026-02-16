# create_tables.py
# Script to create database tables (users and otp_codes)

from sqlalchemy import create_engine, text
import logging

# Logging configuration
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database connection
# postgres://TekoCodes:IQdi4eepCgtBKiBj7KVy8BYjq8SIgqweV1BMdkFMWuEfxpTlIODtcY6zc3MA5c6F@164.68.97.131:5432/academytest
db_user = "postgres"
db_password = "x4IQEBxzpSwDSUIcYxqNfsuEY40jzdrTP5AMKWiDppbAY4kevp0KeL3odvWHqhfE"
db_host = "37.60.236.213"
db_port = "5432"
db_name = "naqwa"

# Use postgresql:// instead of postgresql+psycopg2:// for compatibility
database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(database_url)


def create_grades_table():
    """Create grades table and insert default grades if it doesn't exist"""
    try:
        with engine.begin() as connection:
            # Create grades table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.grades (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert default grades if they don't exist
            grades = [
                "first primary",
                "second primary",
                "third primary",
                "fourth primary",
                "fifth primary",
                "sixth primary",
                "first prep",
                "second prep",
                "third prep",
                "first secondary",
                "second secondary",
                "third secondary"
            ]
            
            for grade in grades:
                connection.execute(text("""
                    INSERT INTO public.grades (name)
                    VALUES (:grade)
                    ON CONFLICT (name) DO NOTHING
                """), {"grade": grade})
            
        logging.info("Grades table created or already exists")
        print("Grades table created or already exists")
        return True
    except Exception as e:
        logging.error(f"Error creating grades table: {e}")
        print(f"Error creating grades table: {e}")
        return False


def add_created_by_to_grades():
    """إضافة عمود created_by لجدول grades (يربط ب admins)."""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE public.grades
                ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES public.admins(id)
            """))
        logging.info("created_by added to grades or already exists")
        return True
    except Exception as e:
        logging.error(f"Error adding created_by to grades: {e}")
        return False


def add_created_by_to_subjects():
    """إضافة عمود created_by لجدول subjects (يربط ب admins)."""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE public.subjects
                ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES public.admins(id)
            """))
        logging.info("created_by added to subjects or already exists")
        return True
    except Exception as e:
        logging.error(f"Error adding created_by to subjects: {e}")
        return False


def add_created_by_to_chapters():
    """إضافة عمود created_by لجدول chapters (يربط ب admins)."""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE public.chapters
                ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES public.admins(id)
            """))
        logging.info("created_by added to chapters or already exists")
        return True
    except Exception as e:
        logging.error(f"Error adding created_by to chapters: {e}")
        return False


def create_users_table():
    """Create users table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL,
                    parent_number VARCHAR(20),
                    birth_date DATE,
                    governorate VARCHAR(100),
                    password VARCHAR(255) NOT NULL,
                    grade VARCHAR(50),
                    section VARCHAR(50),
                    lang_type VARCHAR(50),
                    account_status VARCHAR(50) NOT NULL DEFAULT 'active',
                    points INTEGER DEFAULT 0,
                    early_access BOOLEAN DEFAULT FALSE,
                    subscription_plan VARCHAR(50) DEFAULT 'free',
                    role VARCHAR(50) DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create index on phone_number for faster lookups
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_phone_number 
                ON public.users(phone_number)
            """))
            # إضافة عمود lang_type إن وُجد الجدول مسبقاً بدون العمود
            connection.execute(text("""
                ALTER TABLE public.users
                ADD COLUMN IF NOT EXISTS lang_type VARCHAR(50)
            """))
            
        logging.info("Users table created or already exists (lang_type column ensured)")
        print("Users table created or already exists (lang_type column ensured)")
        return True
    except Exception as e:
        logging.error(f"Error creating users table: {e}")
        print(f"Error creating users table: {e}")
        return False

def create_sessions_table():
    """Create sessions table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    session VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
                )
            """))
            
            # Create index on user_id for faster lookups
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON public.sessions(user_id)
            """))
            
            # Create index on session for faster lookups
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_session 
                ON public.sessions(session)
            """))
            
        logging.info("Sessions table created or already exists")
        print("Sessions table created or already exists")
        return True
    except Exception as e:
        logging.error(f"Error creating sessions table: {e}")
        print(f"Error creating sessions table: {e}")
        return False

def create_admins_table():
    """Create admins table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.admins (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    phone_number VARCHAR(20) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'admin',
                    account_status VARCHAR(50) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("Admins table created or already exists")
        print("Admins table created or already exists")
    except Exception as e:
        logging.error(f"Error creating admins table: {e}")
        print(f"Error creating admins table: {e}")

def create_subjects_table():
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.subjects (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    grade TEXT,
                    stream TEXT,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("Subjects table created or already exists")
        print("Subjects table created or already exists")
    except Exception as e:
        logging.error(f"Error creating subjects table: {e}")
        print(f"Error creating subjects table: {e}")

def create_chapters_table():
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.chapters (
                    id SERIAL PRIMARY KEY,
                    subject_id INTEGER REFERENCES public.subjects(id),
                    name TEXT,
                    order_index INT,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("Chapters table created or already exists")
        print("Chapters table created or already exists")
    except Exception as e:
        logging.error(f"Error creating chapters table: {e}")
        print(f"Error creating chapters table: {e}")

def create_sources_table():
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.sources (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    year INT,
                    grade TEXT,
                    author_name TEXT,
                    published_at DATE,
                    created_by INTEGER NOT NULL REFERENCES public.users(id),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("Sources table created or already exists")
        print("Sources table created or already exists")
    except Exception as e:
        logging.error(f"Error creating sources table: {e}")
        print(f"Error creating sources table: {e}")

def create_questions_table():
    # correct_answer TEXT NOT NULL,
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.questions (
                    id SERIAL PRIMARY KEY,
                    subject_id INTEGER NOT NULL REFERENCES public.subjects(id),
                    chapter_id INTEGER REFERENCES public.chapters(id),
                    question_text TEXT,
                    question_image_url TEXT,
                    question_type TEXT NOT NULL,
                    difficulty INT CHECK (difficulty BETWEEN 1 AND 5),
                    expected_time INT,
                    explanation TEXT,
                    order_index INT,
                    access_level TEXT DEFAULT 'paid',
                    source_id INTEGER REFERENCES public.sources(id),
                    is_common BOOLEAN DEFAULT false,
                    status TEXT DEFAULT 'active',
                    created_by INTEGER NOT NULL REFERENCES public.users(id),
                    reviewed_by INTEGER REFERENCES public.users(id),
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("Questions table created or already exists")
        print("Questions table created or already exists")
    except Exception as e:
        logging.error(f"Error creating questions table: {e}")
        print(f"Error creating questions table: {e}")

def create_question_reports_table():
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.question_reports (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES public.users(id),
                    question_id INTEGER REFERENCES public.questions(id),
                    reason TEXT,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("Question reports table created or already exists")
        print("Question reports table created or already exists")
    except Exception as e:
        logging.error(f"Error creating question_reports table: {e}")
        print(f"Error creating question_reports table: {e}")

def create_question_choices_table():

    """Create question_choices table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.question_choices (
                    id SERIAL PRIMARY KEY,
                    question_id INTEGER REFERENCES public.questions(id),
                    text TEXT NOT NULL,
                    is_correct BOOLEAN DEFAULT FALSE,
                    "order" INTEGER,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("question_choices table created or already exists")
        print("question_choices table created or already exists")
    except Exception as e:
        logging.error(f"Error creating question_choices table: {e}")
        print(f"Error creating question_choices table: {e}")

def create_questions_submissions_table():
    """Create questions_submissions table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.questions_submissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES public.users(id),
                    question_id INTEGER NOT NULL REFERENCES public.questions(id),
                    status TEXT,
                    auto_score FLOAT,
                    manual_score FLOAT,
                    total_score FLOAT,
                    max_score FLOAT,
                    started_at TIMESTAMP,
                    submitted_at TIMESTAMP,
                    graded_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("questions_submissions table created or already exists")
        print("questions_submissions table created or already exists")
    except Exception as e:
        logging.error(f"Error creating questions_submissions table: {e}")
        print(f"Error creating questions_submissions table: {e}")
def create_exams_table():

    """Create exams table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.exams (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    lecture_id INTEGER,
                    course_id INTEGER,
                    duration INTEGER,
                    num_to_show INTEGER,
                    shuffle_questions BOOLEAN DEFAULT FALSE,
                    shuffle_options BOOLEAN DEFAULT FALSE,
                    required BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("exams table created or already exists")
        print("exams table created or already exists")
    except Exception as e:
        logging.error(f"Error creating exams table: {e}")
        print(f"Error creating exams table: {e}")
def create_exams_questions_table():

    """Create exams_questions table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.exams_questions (
                    id SERIAL PRIMARY KEY,
                    exam_id INTEGER NOT NULL REFERENCES public.exams(id),
                    subject_id INTEGER NOT NULL REFERENCES public.subjects(id),
                    chapter_id INTEGER REFERENCES public.chapters(id),
                    question_text TEXT,
                    question_image_url TEXT,
                    question_type TEXT NOT NULL,
                    difficulty INT CHECK (difficulty BETWEEN 1 AND 5),
                    expected_time INT,
                    explanation TEXT,
                    order_index INT,
                    access_level TEXT DEFAULT 'paid',
                    source_id INTEGER REFERENCES public.sources(id),
                    is_common BOOLEAN DEFAULT false,
                    status TEXT DEFAULT 'active',
                    created_by INTEGER NOT NULL REFERENCES public.users(id),
                    reviewed_by INTEGER REFERENCES public.users(id),
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("exams_questions table created or already exists")
        print("exams_questions table created or already exists")
    except Exception as e:
        logging.error(f"Error creating exams_questions table: {e}")
        print(f"Error creating exams_questions table: {e}")



def create_exams_submissions_table():
    """Create exams_submissions table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.exams_submissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES public.users(id),
                    exam_id INTEGER NOT NULL REFERENCES public.exams(id),
                    exam_question_id INTEGER NOT NULL REFERENCES public.exams_questions(id),
                    status TEXT,
                    auto_score FLOAT,
                    manual_score FLOAT,
                    total_score FLOAT,
                    max_score FLOAT,
                    started_at TIMESTAMP,
                    submitted_at TIMESTAMP,
                    graded_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("exams_submissions table created or already exists")
        print("exams_submissions table created or already exists")
    except Exception as e:
        logging.error(f"Error creating exams_submissions table: {e}")
        print(f"Error creating exams_submissions table: {e}")
def create_exam_choises_table():
    """Create exam_choises table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.exam_choises (
                    id SERIAL PRIMARY KEY,
                    exam_question_id INTEGER REFERENCES public.exams_questions(id),
                    text TEXT NOT NULL,
                    is_correct BOOLEAN DEFAULT FALSE,
                    "order" INTEGER,
                    created_at TIMESTAMP DEFAULT now()
                )
            """))
        logging.info("exam_choises table created or already exists")
        print("exam_choises table created or already exists")
    except Exception as e:
        logging.error(f"Error creating exam_choises table: {e}")
        print(f"Error creating exam_choises table: {e}")


def create_site_settings_table():
    """جدول إعدادات الموقع (مثلاً وضع تحت الإنشاء للطلبة)."""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.site_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """))
            connection.execute(text("""
                INSERT INTO public.site_settings (key, value) VALUES ('under_construction', 'true')
                ON CONFLICT (key) DO NOTHING
            """))
        logging.info("site_settings table created or already exists")
        print("site_settings table created or already exists")
    except Exception as e:
        logging.error(f"Error creating site_settings table: {e}")
        print(f"Error creating site_settings table: {e}")


create_grades_table()
create_users_table()
create_sessions_table()
create_admins_table()  # Call this to ensure admins table exists
add_created_by_to_grades()
create_subjects_table()
add_created_by_to_subjects()
create_chapters_table()
add_created_by_to_chapters()
create_sources_table()
create_questions_table()
create_question_reports_table()
create_question_choices_table()  # Call this to ensure question_choices table exists
create_questions_submissions_table()  # Call this to ensure questions_submissions table exists
create_exams_table()  # Call this to ensure exams table exists
create_exams_questions_table()  # Call this to ensure exams_questions table exists
create_exams_submissions_table()  # Call this to ensure exams_submissions table exists
create_exam_choises_table()  # Call this to ensure exam_choises table exists
create_site_settings_table()