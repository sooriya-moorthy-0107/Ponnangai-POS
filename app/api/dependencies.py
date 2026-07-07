from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.domain import User

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
