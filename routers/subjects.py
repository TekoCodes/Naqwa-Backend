# subjects.py
# Endpoint to get available subjects based on user's grade
from fastapi import APIRouter, Header, Query
from sqlalchemy import text
import math
import jwt
import logging
from .users_common import engine, SECRET_KEY, ALGORITHM, create_response

router = APIRouter()

def decode_token_and_get_user(authorization: str):
    """
    Helper function to decode JWT token and get user info
    Returns: (user_id, user_dict) or (None, error_response)
    """
    if not authorization:
        return None, create_response(False, "Authorization header is required", status_code=401)
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None, create_response(False, "Invalid authorization scheme. Use 'Bearer <token>'", status_code=401)
    except ValueError:
        return None, create_response(False, "Invalid authorization header format", status_code=401)
    
    # Decode JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            return None, create_response(False, "Invalid token: user_id not found", status_code=401)
    except jwt.ExpiredSignatureError:
        return None, create_response(False, "Token has expired", status_code=401)
    except jwt.InvalidTokenError as e:
        return None, create_response(False, f"Invalid token: {str(e)}", status_code=401)
    
    # Get user information from database
    with engine.connect() as connection:
        user = connection.execute(
            text("SELECT id, name, grade FROM public.users WHERE id = :user_id"),
            {"user_id": user_id}
        ).mappings().fetchone()
        
        if not user:
            logging.warning(f"User not found for user_id: {user_id}")
            return None, create_response(False, "User not found", status_code=404)
    
    return user_id, user

@router.get("/subjects/available")
def get_available_subjects(authorization: str = Header(None)):
    """
    Get all available subjects for the user's grade level
    Requires JWT token in Authorization header: "Bearer <token>"
    
    Returns:
        JSON response with list of subjects for user's grade
    """
    try:
        user_id, result = decode_token_and_get_user(authorization)
        if not user_id:
            return result
        
        user = result
        grade = user.get("grade")
        
        if not grade:
            logging.warning(f"User grade not set for user_id: {user_id}")
            return create_response(False, "User grade not configured", status_code=400)
        
        # Get all subjects for this grade, ordered by name
        with engine.connect() as connection:
            subjects = connection.execute(
                text("SELECT id, name, grade, stream FROM public.subjects WHERE grade = :grade ORDER BY name"),
                {"grade": grade}
            ).mappings().fetchall()
            
            subjects_list = [
                {
                    "id": subject["id"],
                    "name": subject["name"],
                    "grade": subject["grade"],
                    "stream": subject["stream"]
                }
                for subject in subjects
            ]
            
            logging.info(f"Fetched {len(subjects_list)} subjects for user_id: {user_id}, grade: {grade}")
            
            return create_response(True, "Subjects fetched successfully", {
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "grade": grade
                },
                "subjects": subjects_list,
                "count": len(subjects_list)
            }, status_code=200)
    
    except Exception as e:
        logging.error(f"Error in get_available_subjects: {str(e)}")
        return create_response(False, f"An error occurred: {str(e)}", status_code=500)


@router.get("/subjects/{subject_id}/chapters")
def get_subject_chapters(subject_id: int, authorization: str = Header(None)):
    """
    Get all chapters for a specific subject
    Requires JWT token in Authorization header: "Bearer <token>"
    
    Args:
        subject_id: ID of the subject
        authorization: JWT token
    
    Returns:
        JSON response with list of chapters for the subject
    """
    try:
        user_id, result = decode_token_and_get_user(authorization)
        if not user_id:
            return result
        
        user = result
        grade = user.get("grade")
        
        if not grade:
            logging.warning(f"User grade not set for user_id: {user_id}")
            return create_response(False, "User grade not configured", status_code=400)
        
        with engine.connect() as connection:
            # First, verify subject exists and belongs to user's grade
            subject = connection.execute(
                text("SELECT id, name, grade FROM public.subjects WHERE id = :subject_id AND grade = :grade"),
                {"subject_id": subject_id, "grade": grade}
            ).mappings().fetchone()
            
            if not subject:
                logging.warning(f"Subject {subject_id} not found or not available for grade {grade}")
                return create_response(False, "Subject not found or not available for your grade", status_code=404)
            
            # Get all chapters for this subject, ordered by order_index
            chapters = connection.execute(
                text("""
                    SELECT id, subject_id, name, order_index, created_at 
                    FROM public.chapters 
                    WHERE subject_id = :subject_id 
                    ORDER BY order_index ASC, name ASC
                """),
                {"subject_id": subject_id}
            ).mappings().fetchall()
            
            chapters_list = [
                {
                    "id": chapter["id"],
                    "subject_id": chapter["subject_id"],
                    "name": chapter["name"],
                    "order": chapter["order_index"]
                }
                for chapter in chapters
            ]
            
            logging.info(f"Fetched {len(chapters_list)} chapters for subject_id: {subject_id}, user_id: {user_id}")
            
            return create_response(True, "Chapters fetched successfully", {
                "subject": {
                    "id": subject["id"],
                    "name": subject["name"],
                    "grade": subject["grade"]
                },
                "chapters": chapters_list,
                "count": len(chapters_list)
            }, status_code=200)
    
    except Exception as e:
        logging.error(f"Error in get_subject_chapters: {str(e)}")
        return create_response(False, f"An error occurred: {str(e)}", status_code=500)


@router.get("/subjects/{subject_id}/questions")
def get_subject_questions(
    subject_id: int,
    page: int = Query(1, ge=1, description="رقم الصفحة"),
    chapter_id: int = Query(None, description="فلتر حسب الفصل (اختياري)"),
    authorization: str = Header(None)
):
    """
    جلب الأسئلة مع تقسيمها بيدجات (50 سؤال في كل صفحة)
    Requires JWT token in Authorization header: "Bearer <token>"
    
    Args:
        subject_id: رقم المادة
        page: رقم الصفحة (افتراضي 1)
        chapter_id: رقم الفصل (اختياري - للفلترة حسب الفصل)
    
    Returns:
        JSON response مع 50 سؤال في كل صفحة
    """
    try:
        user_id, result = decode_token_and_get_user(authorization)
        if not user_id:
            return result
        
        user = result
        grade = user.get("grade")
        
        if not grade:
            logging.warning(f"User grade not set for user_id: {user_id}")
            return create_response(False, "User grade not configured", status_code=400)
        
        per_page = 50
        offset = (page - 1) * per_page
        
        with engine.connect() as connection:
            # التحقق من أن المادة موجودة وتنتمي لصف المستخدم
            subject = connection.execute(
                text("SELECT id, name, grade FROM public.subjects WHERE id = :subject_id AND grade = :grade"),
                {"subject_id": subject_id, "grade": grade}
            ).mappings().fetchone()
            
            if not subject:
                logging.warning(f"Subject {subject_id} not found or not available for grade {grade}")
                return create_response(False, "Subject not found or not available for your grade", status_code=404)
            
            # بناء الاستعلام مع فلتر الفصل اختياري
            where_clause = "WHERE q.subject_id = :subject_id AND q.status = 'active'"
            params = {"subject_id": subject_id, "limit": per_page, "offset": offset}
            params_count = {"subject_id": subject_id}
            
            if chapter_id:
                where_clause += " AND q.chapter_id = :chapter_id"
                params["chapter_id"] = chapter_id
                params_count["chapter_id"] = chapter_id
            
            # جلب إجمالي عدد الأسئلة
            count_query = text(f"""
                SELECT COUNT(*) as total FROM public.questions q {where_clause}
            """)
            total_result = connection.execute(count_query, params_count).mappings().fetchone()
            total_count = total_result["total"] or 0
            total_pages = math.ceil(total_count / per_page) if total_count > 0 else 0
            
            # جلب الأسئلة مع الـ pagination
            questions_query = text(f"""
                SELECT q.id, q.subject_id, q.chapter_id, q.question_text, q.question_image_url,
                       q.question_type, q.difficulty, q.expected_time, q.explanation, q.order_index
                FROM public.questions q
                {where_clause}
                ORDER BY q.order_index ASC NULLS LAST, q.id ASC
                LIMIT :limit OFFSET :offset
            """)
            questions_rows = connection.execute(questions_query, params).mappings().fetchall()
            
            questions_list = []
            for q in questions_rows:
                # جلب الاختيارات لكل سؤال
                choices = connection.execute(
                    text("""
                        SELECT id, text, is_correct, "order"
                        FROM public.question_choices
                        WHERE question_id = :question_id
                        ORDER BY "order" ASC NULLS LAST, id ASC
                    """),
                    {"question_id": q["id"]}
                ).mappings().fetchall()
                
                choices_list = [
                    {"id": c["id"], "text": c["text"], "is_correct": c["is_correct"], "order": c["order"]}
                    for c in choices
                ]
                
                questions_list.append({
                    "id": q["id"],
                    "subject_id": q["subject_id"],
                    "chapter_id": q["chapter_id"],
                    "question_text": q["question_text"],
                    "question_image_url": q["question_image_url"],
                    "question_type": q["question_type"],
                    "difficulty": q["difficulty"],
                    "expected_time": q["expected_time"],
                    "explanation": q["explanation"],
                    "order_index": q["order_index"],
                    "choices": choices_list
                })
            
            logging.info(f"Fetched page {page} with {len(questions_list)} questions for subject_id: {subject_id}, user_id: {user_id}")
            
            return create_response(True, "Questions fetched successfully", {
                "questions": questions_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                },
                "count": len(questions_list)
            }, status_code=200)
    
    except Exception as e:
        logging.error(f"Error in get_subject_questions: {str(e)}")
        return create_response(False, f"An error occurred: {str(e)}", status_code=500)
