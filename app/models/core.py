from sqlmodel import SQLModel, Session


class DBModelBase(SQLModel):
    def save(self, db: Session):
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    def delete(self, db: Session):
        db.delete(self)
        db.commit()

    def update(self, db: Session, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)
        self.save(db)
        return self
