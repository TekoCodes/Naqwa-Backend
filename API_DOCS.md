# Naqwa API Documentation

توثيق كامل لجميع الـ Endpoints لإعادة بناء الباك إند بـ Node.js + Express + TypeScript + Drizzle + PostgreSQL.

---

## Base URL

جميع الـ endpoints تحت البريفكس: `/api/v1`

---

## Response Format الموحد

```json
{
  "success": boolean,
  "message": string,
  ...data  // حقول إضافية حسب الـ endpoint
}
```

- عند النجاح: `success: true` وعادة `status_code: 200`
- عند الفشل: `success: false` مع `message` يصف السبب

---

## Authentication

### JWT Token
- **Header:** `Authorization: Bearer <token>`
- **Payload:** `{ user_id, created_at (ISO string), role, exp }`
- **Algorithm:** HS256
- **Expiry:** 60 دقيقة
- **SECRET_KEY:** يُستخدم في التشفير (غيّره في البرودكشن)

### Roles
- `user` أو `student` — الطالب
- `admin` — الأدمن (يستمد من جدول `admins`)

---

## 1. Auth & Users (عام — بدون توكن)

### POST /api/v1/login
تسجيل دخول الطالب.

**Request Body:**
```json
{
  "phone_number": "01xxxxxxxxx",  // أو email (اختياري - أحدهما مطلوب)
  "email": "optional@email.com",
  "password": "string"            // مطلوب
}
```

**Validation:**
- `phone_number` أو `email` واحد منهما مطلوب
- `password` مطلوب
- رقم التليفون: 11 رقم، يبدأ بـ 010 أو 011 أو 012 أو 015 (يُزال المسافات)

**Response Success (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "jwt_token_string",
  "token_type": "bearer"
}
```

**Errors:** 400 (بيانات ناقصة/غير صحيحة), 401 (Invalid credentials)

---

### POST /api/v1/register
إنشاء حساب طالب جديد.

**Request Body:**
```json
{
  "name": "string",               // الاسم الرباعي
  "phone_number": "01xxxxxxxxx",  // 11 رقم مصري
  "parent_number": "01xxxxxxxxx", // 11 رقم مصري
  "password": "string",           // كلمة مرور
  "birth_date": "YYYY-MM-DD",     // تاريخ الميلاد
  "governorate": "string",        // محافظة مصرية (من القائمة)
  "grade": "S1" | "S2" | "S3",   // الصف
  "section": "علمي رياضه" | "علمي علوم" | "ادبي",
  "lang_type": "عربي" | "لغات"
}
```

**Validation:**
- جميع الحقول مطلوبة
- `grade`: S1, S2, S3
- `section`: علمي رياضه، علمي علوم، ادبي
- `lang_type`: عربي، لغات
- `governorate`: من قائمة المحافظات المصرية
- `phone_number` يجب ألا يكون مسجلاً مسبقاً

**Response Success (200):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "token": "jwt_token_string",
  "token_type": "bearer"
}
```

**Errors:** 400, 409 (رقم التليفون مستخدم)

---

### POST /api/v1/forgot-password
استعادة كلمة المرور (مع OTP للبريد إن وُجد).

**Request Body:**
```json
{
  "phone_number": "01xxxxxxxxx",  // أو email
  "email": "optional@email.com",
  "otp": "string",                // مطلوب — كود OTP
  "new_password": "string"        // مطلوب
}
```

**Validation:**
- `phone_number` أو `email` واحد منهما مطلوب
- `otp` و `new_password` مطلوبان
- إن استُخدم `email`: يُتحقق من OTP في جدول `otp_codes` (code, email, used=false, expires_at > now)

**Response Success (200):**
```json
{
  "success": true,
  "message": "Password updated successfully"
}
```

**Errors:** 400, 404 (مستخدم غير موجود)

---

### POST /api/v1/admin/login
تسجيل دخول الأدمن.

**Request Body:**
```json
{
  "phone_number": "01xxxxxxxxx",
  "password": "string"
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "jwt_token_string",
  "token_type": "bearer"
}
```

**Errors:** 400, 401

---

## 2. Token Verification (يتطلب توكن أي مستخدم)

### GET /api/v1/verify
التحقق من صلاحية التوكن.

**Headers:** `Authorization: Bearer <token>`

**Response Success (200):**
```json
{
  "success": true,
  "message": "Token is valid",
  "user_id": number,
  "role": "user" | "admin",
  "created_at": "ISO string",
  "name": "string | null"
}
```

**Errors:** 401 (توكن غير صالح أو منتهي)

---

## 3. Student Profile (يتطلب توكن طالب)

### GET /api/v1/student/profile
جلب بيانات الطالب المسجل دخوله.

**Headers:** `Authorization: Bearer <token>`

**Response Success (200):**
```json
{
  "success": true,
  "message": "Profile retrieved",
  "profile": {
    "name": "string",
    "phone_number": "string",
    "parent_number": "string",
    "birth_date": "YYYY-MM-DD",
    "governorate": "string",
    "grade": "string",
    "section": "string",
    "lang_type": "string"
  }
}
```

---

### PATCH /api/v1/student/profile
تحديث بيانات الطالب.

**Headers:** `Authorization: Bearer <token>`

**Request Body (كل الحقول اختيارية — يُرسل ما يُراد تحديثه فقط):**
```json
{
  "name": "string",
  "phone_number": "string",
  "parent_number": "string",
  "birth_date": "YYYY-MM-DD",
  "governorate": "string",
  "grade": "S1" | "S2" | "S3",
  "section": "علمي رياضه" | "علمي علوم" | "ادبي",
  "lang_type": "عربي" | "لغات"
}
```

**Validation:**
- `grade`: S1, S2, S3
- `section`: علمي رياضه، علمي علوم، ادبي
- `lang_type`: عربي، لغات
- `phone_number` يُفحص للتأكد من عدم تكراره مع مستخدم آخر

**Response Success (200):**
```json
{
  "success": true,
  "message": "تم تحديث البيانات بنجاح"
}
```

**Errors:** 400, 401, 409 (رقم التليفون مستخدم)

---

## 4. Dashboard (يتطلب توكن طالب)

### GET /api/v1/dashboard/stats
إحصائيات داشبورد الطالب: أسئلة وامتحانات محلولة، نسبة التقدم.

**Headers:** `Authorization: Bearer <token>`

**Response Success (200):**
```json
{
  "success": true,
  "message": "Dashboard stats",
  "total_questions": number,
  "solved_questions": number,
  "total_exams": number,
  "solved_exams": number,
  "progress_percent": number
}
```

- `progress_percent` = متوسط نسبة الأسئلة والامتحانات المحلولة

---

## 5. Subjects (يتطلب توكن طالب)

### GET /api/v1/subjects/available
المواد المتاحة لصف الطالب.

**Headers:** `Authorization: Bearer <token>`

**Response Success (200):**
```json
{
  "success": true,
  "message": "Subjects fetched successfully",
  "user": { "id": number, "name": "string", "grade": "string" },
  "subjects": [
    { "id": number, "name": "string", "grade": "string", "stream": "string" }
  ],
  "count": number
}
```

---

### GET /api/v1/subjects/with-counts
المواد مع أعداد الشاباتر والأسئلة والامتحانات.

**Headers:** `Authorization: Bearer <token>`

**Response Success (200):**
```json
{
  "success": true,
  "message": "Subjects with counts",
  "subjects": [
    {
      "id": number,
      "name": "string",
      "grade": "string",
      "stream": "string",
      "chapters_count": number,
      "questions_count": number,
      "exams_count": number
    }
  ],
  "grade": "string",
  "count": number
}
```

---

### GET /api/v1/subjects/:subject_id/chapters
فصول مادة معينة.

**Headers:** `Authorization: Bearer <token>`

**Params:** `subject_id` (path) — رقم المادة

**Response Success (200):**
```json
{
  "success": true,
  "message": "Chapters fetched successfully",
  "subject": { "id": number, "name": "string", "grade": "string" },
  "chapters": [
    { "id": number, "subject_id": number, "name": "string", "order": number }
  ],
  "count": number
}
```

---

### GET /api/v1/subjects/:subject_id/questions
أسئلة مادة معينة مع pagination.

**Headers:** `Authorization: Bearer <token>`

**Params:**
- `subject_id` (path) — رقم المادة
- `page` (query, default 1) — رقم الصفحة
- `chapter_id` (query, optional) — فلتر حسب الفصل

**Response Success (200):**
```json
{
  "success": true,
  "message": "Questions fetched successfully",
  "questions": [
    {
      "id": number,
      "subject_id": number,
      "chapter_id": number | null,
      "question_text": "string",
      "question_image_url": "string | null",
      "question_type": "string",
      "difficulty": number,
      "expected_time": number | null,
      "explanation": "string | null",
      "order_index": number | null,
      "choices": [
        { "id": number, "text": "string", "is_correct": boolean, "order": number }
      ]
    }
  ],
  "pagination": {
    "page": number,
    "per_page": 50,
    "total_count": number,
    "total_pages": number,
    "has_next": boolean,
    "has_prev": boolean
  },
  "count": number
}
```

---

## 6. Site Status (عام + أدمن)

### GET /api/v1/site-status
عام — لا يتطلب توكن. حالة وضع "تحت الإنشاء".

**Response Success (200):**
```json
{
  "success": true,
  "message": "OK",
  "under_construction": boolean
}
```

---

### GET /api/v1/admin/site-status
أدمن فقط — قراءة إعداد وضع تحت الإنشاء.

**Headers:** `Authorization: Bearer <token>` (role = admin)

**Response Success (200):**
```json
{
  "success": true,
  "message": "OK",
  "data": { "under_construction": boolean }
}
```

---

### PUT /api/v1/admin/site-status
أدمن فقط — تحديث وضع تحت الإنشاء.

**Headers:** `Authorization: Bearer <token>` (role = admin)

**Request Body:**
```json
{
  "under_construction": boolean
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "تم التحديث",
  "data": { "under_construction": boolean }
}
```

---

## 7. Admin CRUD — Grades (أدمن فقط)

**Headers:** `Authorization: Bearer <token>` (role = admin)

### GET /api/v1/admin/grades
قائمة كل الـ grades.

**Response:** `{ success, message, data: [{ id, name, created_at, created_by, created_by_name }] }`

### POST /api/v1/admin/grades
إنشاء grade.

**Body:** `{ "name": "string" }`

**Response:** `{ success, message, data: { id, name, created_at, created_by } }`

### PUT /api/v1/admin/grades/:grade_id
تحديث grade.

**Body:** `{ "name": "string" }`

### DELETE /api/v1/admin/grades/:grade_id
حذف grade.

---

## 8. Admin CRUD — Subjects (أدمن فقط)

### GET /api/v1/admin/subjects
قائمة كل المواد.

**Response:** `{ success, message, data: [{ id, name, grade, stream, created_at, created_by, created_by_name }] }`

### POST /api/v1/admin/subjects
إنشاء مادة.

**Body:**
```json
{
  "name": "string",
  "grade": "string | null",
  "stream": "string | null"
}
```

### PUT /api/v1/admin/subjects/:subject_id
تحديث مادة.

**Body:** `{ "name": "string | null", "grade": "string | null", "stream": "string | null" }` (كلها اختيارية)

### DELETE /api/v1/admin/subjects/:subject_id
حذف مادة.

---

## 9. Admin CRUD — Chapters (أدمن فقط)

### GET /api/v1/admin/chapters
قائمة كل الفصول.

**Response:** `{ success, message, data: [{ id, subject_id, name, order_index, created_at, created_by, subject_name, created_by_name }] }`

### POST /api/v1/admin/chapters
إنشاء فصل.

**Body:**
```json
{
  "subject_id": number,
  "name": "string",
  "order_index": number | null
}
```

### PUT /api/v1/admin/chapters/:chapter_id
تحديث فصل.

**Body:** `{ "subject_id": number | null, "name": "string | null", "order_index": number | null }`

### DELETE /api/v1/admin/chapters/:chapter_id
حذف فصل.

---

## 10. Admin CRUD — Sources (أدمن فقط)

### GET /api/v1/admin/sources
قائمة كل المصادر.

**Response:** `{ success, message, data: [{ id, name, source_type, year, grade, author_name, published_at, created_by, notes, created_at, created_by_name }] }`

### POST /api/v1/admin/sources
إنشاء مصدر.

**Body:**
```json
{
  "name": "string",
  "source_type": "string",
  "year": number | null,
  "grade": "string | null",
  "author_name": "string | null",
  "published_at": "YYYY-MM-DD | null",
  "notes": "string | null",
  "created_by": number
}
```

### PUT /api/v1/admin/sources/:source_id
تحديث مصدر.

**Body:** كل الحقول اختيارية (name, source_type, year, grade, author_name, published_at, notes)

### DELETE /api/v1/admin/sources/:source_id
حذف مصدر.

---

## 11. Admin CRUD — Users (أدمن فقط)

### GET /api/v1/admin/users
قائمة كل المستخدمين (الطلبة).

**Response:** `{ success, message, data: [{ id, name, phone_number, parent_number, birth_date, governorate, grade, section, lang_type, account_status, points, early_access, subscription_plan, role, created_at }] }`

### GET /api/v1/admin/users/:user_id
تفاصيل مستخدم واحد.

### PUT /api/v1/admin/users/:user_id
تحديث مستخدم.

**Body:** كل الحقول اختيارية:
```json
{
  "name": "string",
  "phone_number": "string",
  "parent_number": "string",
  "birth_date": "YYYY-MM-DD",
  "governorate": "string",
  "grade": "string",
  "section": "string",
  "lang_type": "string",
  "account_status": "string",
  "points": number,
  "subscription_plan": "string",
  "role": "string"
}
```

### DELETE /api/v1/admin/users/:user_id
حذف مستخدم.

---

## Validation Rules (للإعادة في Node.js)

### Phone Number
- 11 رقم بالضبط
- يبدأ بـ 010 أو 011 أو 012 أو 015
- إزالة المسافات قبل التحقق

### Governorate
- من قائمة المحافظات المصرية (عربي أو إنجليزي)
- قائمة: القاهرة، الجيزة، الإسكندرية، الدقهلية، البحر الأحمر، البحيرة، الفيوم، الغربية، الإسماعيلية، المنوفية، المنيا، القليوبية، الوادي الجديد، السويس، أسوان، أسيوط، بني سويف، بورسعيد، دمياط، الشرقية، جنوب سيناء، كفر الشيخ، مطروح، الأقصر، قنا، شمال سيناء، سوهاج + الإنجليزية

### Password
- تشفير: bcrypt (12 rounds)
- التحقق: passlib.verify أو bcrypt.compare

---

## Database Schema (ملخص لـ Drizzle)

### users
- id, name, phone_number, parent_number, birth_date, governorate, password, grade, section, lang_type, account_status, points, early_access, subscription_plan, role, created_at

### admins
- id, name, phone_number, password, role, account_status, created_at

### sessions
- id, user_id, session (token string), created_at, active

### grades
- id, name, created_at, created_by (FK admins)

### subjects
- id, name, grade, stream, created_at, created_by (FK admins)

### chapters
- id, subject_id, name, order_index, created_at, created_by (FK admins)

### sources
- id, name, source_type, year, grade, author_name, published_at, created_by (FK users), notes, created_at

### questions
- id, subject_id, chapter_id, question_text, question_image_url, question_type, difficulty, expected_time, explanation, order_index, status, created_by, ...

### question_choices
- id, question_id, text, is_correct, order

### exams, exams_questions, exams_submissions, exam_choises
- (للإكمال عند الحاجة)

### questions_submissions
- user_id, question_id, status, auto_score, ...

### site_settings
- key (PK), value

### otp_codes
- email, code, used, expires_at (لـ forgot-password بالبريد)

---

## CORS
- Origins مسموح: http://localhost:5173, http://127.0.0.1:5173, http://localhost:3000
- credentials: true
- methods: *
- headers: *
