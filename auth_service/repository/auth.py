from fastapi import HTTPException, status
from auth_service import models, schemas
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, not_
from auth_service.utils import cryptoUtil
from datetime import datetime, timedelta

## ---------------------------- Auth CRUD Operations-------------------------------
## To create new token for a password reset
def create_reset_code(request: schemas.EmailRequest, reset_code: str, db: Session):
    # Create the query
    query = text("""INSERT INTO codes(email, reset_code, status, expired_in) 
                    VALUES (:email, :reset_code, :status, :expired_in)""")
    
    # Execute the query with parameters
    db.execute(query, {
        'email': request.email,
        'reset_code': reset_code,
        'status': True,
        'expired_in': datetime.now() + timedelta(hours=8)
    })
    db.commit()

    return {"Message": f"Reset Code created successfully for User with email {request.email}."}

## Replacing the old password with the new password for the given email
def reset_password(new_password: str, email: str, db: Session):
    # Create the query
    query = text("""UPDATE users SET password=:password WHERE email=:email""")
    
    # Execute the query with parameters
    db.execute(query, {
        'password': cryptoUtil.get_hash(new_password),
        'email': email
    })
    db.commit()

    return {"Message": f"Password reset successful for User with email {email}."}

## Disable the reset token for the user after a successful password reset
def disable_reset_code(reset_password_token: str, email: str, db: Session):
    # Create the query
    query = text("""UPDATE codes 
                    SET status=:new_status 
                    WHERE 
                        status=:current_status 
                    AND 
                        (reset_code=:reset_code OR email=:email)""")
    
    # Execute the query with parameters
    db.execute(query, {
        'new_status': False,
        'current_status': True,
        'reset_code': reset_password_token,
        'email': email
    })
    db.commit()

    return {"Message": f"Reset code successfully disabled for User with email - {email}."}

## Finding if the user with the given email exists or not
def find_existed_user(email: str, db: Session):
    user = db.query(models.User).filter(and_(models.User.email == email, models.User.is_active == True)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Either user with email {email} not found OR currently inactive !")
    return user

## Checking if the JWT token is used before and the user is no longer active
def find_token_black_lists(token: str, db: Session):
    token = db.query(models.Blacklists).filter(models.Blacklists.token == token).first()
    return True if token else False

## To check if the password reset token is valid or not
def check_reset_password_token(token: str, db: Session):
    # Create the query
    query = text("""SELECT email FROM codes
                    WHERE
                        status=:status
                    AND
                        reset_code=:reset_code
                    AND
                        expired_in >= CURRENT_TIMESTAMP""")
    
    # Execute the query with parameters
    resultproxy = db.execute(query, {
        'status': True,
        'reset_code': token
    })

    # The end result is the list which contains query results in tuple format
    return [rowproxy for rowproxy in resultproxy]
