import models
from sqlalchemy.orm import Session
from database import SessionLocal

class UserManager:
    def __init__(self):
        self.userid = None

    def get_userinfo(self, db: Session, email: str, password: str):
        try:
            user = db.query(models.User)\
                .filter(models.User.email == email)\
                .filter(models.User.password == password)\
                .first()
            return user
        except Exception as e:
            print(e)
            return None


    def create_user(self, db: Session, firstname: str, lastname: str, email: str, usertype: str, password: str):
        try:
            user_exists = db.query(models.User).filter(models.User.email == email).first()
            if user_exists:
                return False

            new_user = models.User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                user_type=usertype,
                password=password  # Remember to hash this before storing
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            self.userid = new_user.userid
            return True
        
        except Exception as e:
            print(e)
            return False
        

if __name__ == "__main__":
    dbmgr = UserManager()

    print(dbmgr.create_user('Atharva', 'Test3', 'test@user.com', 'PATIENT', '12345678'))
    print(dbmgr.create_user('Atharva', 'Test4', 'test@user1.com', 'RESEARCHER', '12345678'))
    user = dbmgr.get_userinfo('test@user1.com', '12345678')
    print(user.userid)
