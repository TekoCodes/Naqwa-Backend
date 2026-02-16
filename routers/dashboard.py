# dashboard.py — إحصائيات داشبورد الطالب
from fastapi import APIRouter, Header
from sqlalchemy import text
import logging
from .users_common import engine, create_response
from .subjects import decode_token_and_get_user

router = APIRouter()


@router.get("/dashboard/stats")
def get_dashboard_stats(authorization: str = Header(None)):
    """
    إحصائيات الداشبورد: أسئلة محلولة، امتحانات محلولة، مستوى التقدم.
    يتطلب: Authorization: Bearer <token>
    """
    try:
        user_id, result = decode_token_and_get_user(authorization)
        if not user_id:
            return result

        user = result
        grade = user.get("grade")
        if not grade:
            return create_response(False, "User grade not configured", status_code=400)

        with engine.connect() as conn:
            # 1) إجمالي الأسئلة (فردية) للمواد الخاصة بالطالب
            total_q = conn.execute(
                text("""
                    SELECT COUNT(*) AS c FROM public.questions q
                    WHERE q.subject_id IN (SELECT id FROM public.subjects WHERE grade = :grade)
                    AND q.status = 'active'
                """),
                {"grade": grade},
            ).scalar() or 0

            # 2) أسئلة محلولة (فردية) للطالب
            solved_q = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT qs.question_id) AS c
                    FROM public.questions_submissions qs
                    JOIN public.questions q ON q.id = qs.question_id
                    WHERE q.subject_id IN (SELECT id FROM public.subjects WHERE grade = :grade)
                    AND qs.user_id = :user_id
                """),
                {"grade": grade, "user_id": user_id},
            ).scalar() or 0

            # 3) إجمالي الامتحانات (نشطة) للمواد الخاصة بالطالب
            total_e = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT eq.exam_id) AS c
                    FROM public.exams_questions eq
                    JOIN public.subjects s ON s.id = eq.subject_id
                    JOIN public.exams e ON e.id = eq.exam_id
                    WHERE s.grade = :grade AND e.is_active = true
                """),
                {"grade": grade},
            ).scalar() or 0

            # 4) امتحانات محلولة للطالب (من نفس مجموعة الامتحانات)
            solved_e = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT es.exam_id) AS c
                    FROM public.exams_submissions es
                    JOIN public.exams_questions eq ON eq.exam_id = es.exam_id
                    JOIN public.subjects s ON s.id = eq.subject_id
                    JOIN public.exams e ON e.id = es.exam_id
                    WHERE s.grade = :grade AND e.is_active = true AND es.user_id = :user_id
                """),
                {"grade": grade, "user_id": user_id},
            ).scalar() or 0

        # 5) مستوى التقدم (نسبة مئوية)
        ratio_q = (solved_q / total_q) if total_q else 0
        ratio_e = (solved_e / total_e) if total_e else 0
        progress_percent = round((ratio_q + ratio_e) / 2 * 100, 1)

        return create_response(
            True,
            "Dashboard stats",
            {
                "total_questions": total_q,
                "solved_questions": solved_q,
                "total_exams": total_e,
                "solved_exams": solved_e,
                "progress_percent": progress_percent,
            },
            status_code=200,
        )
    except Exception as e:
        logging.error(f"Error in get_dashboard_stats: {e}")
        return create_response(False, str(e), status_code=500)
