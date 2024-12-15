from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from DBManager import UserManager

app = FastAPI()
user_db = UserManager()
models.Base.metadata.create_all(bind=database.engine)


def connect_db():
    db = database.SessionLocal()

    try:
        yield db

    finally:
        db.close()


@app.get("/")
def root():
    return "API is active"


@app.post("/users/", response_model=schemas.UserRead)
def create_user(user: schemas.UserCreate, db: Session = Depends(connect_db)):
    success = user_db.create_user(
        db=db,
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        usertype=user.user_type,
        password=user.password
    )
    if not success:
        raise HTTPException(status_code=409, detail=f"User account already exists with email {user.email}")

    new_user = db.query(models.User).filter(models.User.email == user.email).first()
    return new_user


@app.post("/userdetails/", response_model=schemas.UserRead)
def find_user(user: schemas.UserFind, db: Session = Depends(connect_db)):
    user_data = user_db.get_userinfo(
        db=db,
        email=user.email,
        password=user.password
    )
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found or invalid credentials")
    
    return user_data



# Read user by ID
@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: str, db: Session = Depends(connect_db)):
    user = db.query(models.User).filter(models.User.userid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    


# # Create activity log
# @app.post("/activity_logs/", response_model=schemas.ActivityLogCreate)
# def create_activity_log(log: schemas.ActivityLogCreate, db: Session = Depends(connect_db)):
#     db_log = models.ActivityLog(userid=log.userid, ip_address=log.ip_address)
#     db.add(db_log)
#     db.commit()
#     db.refresh(db_log)
#     return log


# # Read user logs
# @app.get("/user_logs/{user_id}", response_model=schemas.UserLogRead)
# def get_user_log(user_id: str, db: Session = Depends(connect_db)):
#     log = db.query(models.UserLog).filter(models.UserLog.userid == user_id).first()
#     if not log:
#         raise HTTPException(status_code=404, detail="User log not found")
#     return log


# # Update user logs
# @app.put("/user_logs/{user_id}", response_model=schemas.UserLogRead)
# def update_user_log(user_id: str, log_update: schemas.UserLogUpdate, db: Session = Depends(connect_db)):
#     log = db.query(models.UserLog).filter(models.UserLog.userid == user_id).first()
#     if not log:
#         raise HTTPException(status_code=404, detail="User log not found")
#     for key, value in log_update.dict(exclude_unset=True).items():
#         setattr(log, key, value)
#     db.commit()
#     db.refresh(log)
#     return log
