import base64
import os
from io import BytesIO
import pyqrcode
from fastapi import HTTPException, status
from auth_service import models, schemas
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from auth_service.utils import cryptoUtil, otpUtil

## For creating a New user
def create(request: schemas.CreateUser, db: Session):
    new_user = models.User(
        full_name=request.full_name,
        email=request.email,
        password=cryptoUtil.get_hash(request.password),
        tfa_secret=base64.b32encode(os.urandom(32)).decode('utf-8')
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

## For getting the basic details of the user based on the ID
def get_user_profile(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found !")
    return user

## For updating the basic info of the user 
def update(id: int, request: schemas.UpdateUserBasicInfo, db: Session):
    user_query = db.query(models.User).filter(models.User.id == id)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    
    user_data = request.model_dump(exclude_unset=True)

    ## Columns to be updated
    columns = {}
    for key, value in user_data.items():
        if key.lower() == "password":
            columns[key] = cryptoUtil.get_hash(value)
        else:
            columns[key] = value
    columns["updated_on"] = datetime.now(timezone.utc)

    # Building the SET clause
    set_clause = ", ".join([f"{key} = :{key}" for key in columns.keys()])

    # Creating the query
    query = text(f"UPDATE users SET {set_clause} WHERE id = :id")

    # Adding id to the columns dictionary
    columns["id"] = id

    # Executing the query with parameters
    db.execute(query, columns)
    db.commit()
    
    return {"Message": f"User with id {id} updated successfully"}

## For Deleting the user 
def delete(id: int, db: Session):
    user_query = db.query(models.User).filter(models.User.id == id)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    user_query.delete(synchronize_session=False)
    db.commit()
    return {"Message": f"User with id {id} deleted successfully"}

## For getting the all the user details 
def get_all_user_profile(db: Session):
    users = db.query(models.User).all()
    return users

## For updating the password for current user based on the Email
def change_password(email: str, request: schemas.ChangePassword, db: Session):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email '{email}' not found")
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"New Password & Confirm Password doesn't match. !")

    if not cryptoUtil.verify(request.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Incorrect Old Password. !")
    
    query = text("""UPDATE users SET password=:password, updated_on=:updated_on WHERE email=:email""")
    db.execute(query, {
        'password': cryptoUtil.get_hash(request.new_password),
        'updated_on': datetime.now(timezone.utc),
        'email': email
    })
    db.commit()
    
    return {"Message": f"Password for User with email {email} updated successfully"}

## For Reseting the password for user based on the ID
def reset_password(id: int, request: schemas.ResetPassword, db: Session):
    user_query = db.query(models.User).filter(models.User.id == id)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id '{id}' not found")
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"New Password & Confirm Password doesn't match. !")
    
    query = text("""UPDATE users SET password=:password, updated_on=:updated_on WHERE id=:id""")
    db.execute(query, {
        'password': cryptoUtil.get_hash(request.new_password),
        'updated_on': datetime.now(timezone.utc),
        'id': id
    })
    db.commit()
    
    return {"Message": f"Password reset was successful for User with id {id}."}

## Blacklist the token so it can't be used further and update the active status of the user
def set_black_list(token: str, currentUser: schemas.User, db: Session):
    blacklist_entry = models.Blacklists(
        token=token,
        email=currentUser.email
    )
    db.add(blacklist_entry)
    db.commit()
    db.refresh(blacklist_entry)

    query = text("""UPDATE users SET is_active=:is_active, updated_on=:updated_on WHERE email=:email""")
    db.execute(query, {
        'is_active': False,
        'updated_on': datetime.now(timezone.utc),
        'email': currentUser.email
    })
    db.commit()

    return blacklist_entry

## Generate the QR for registering the user in an Authenticator app
def get_2fa_qr(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found !")
    
    data = f"""otpauth://totp/<AppName>-2FA:{user.email}?secret={user.tfa_secret}&issuer=<Client-App-Name>"""
    url = pyqrcode.create(data)
    stream = BytesIO()
    url.png(stream, scale=3)
    return {"data": base64.b64encode(stream.getvalue()).decode('utf-8')}

## For enabling the 2FA status of the user 
def enable_2fa(id: int, request: schemas.Enable2FA, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    
    if bool(user.tfa_enabled):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="2FA already enabled !!!")
    
    if not otpUtil.verify_otp(user.tfa_secret, request.otp):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Incorrect OTP. !")

    query = text("""UPDATE users SET tfa_enabled=:tfa_enabled, updated_on=:updated_on WHERE id=:id""")
    db.execute(query, {
        'tfa_enabled': True,
        'updated_on': datetime.now(timezone.utc),
        'id': id
    })
    db.commit()
    
    return {"Message": f"2FA is enabled for the User with id {id}."}

## For disabling the 2FA for the user 
def disable_2fa(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    
    if not bool(user.tfa_enabled):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="2FA already disabled !!!")

    query = text("""UPDATE users SET tfa_enabled=:tfa_enabled, updated_on=:updated_on WHERE id=:id""")
    db.execute(query, {
        'tfa_enabled': False,
        'updated_on': datetime.now(timezone.utc),
        'id': id
    })
    db.commit()
    
    return {"Message": f"2FA is Disabled for the User with id {id}."}
