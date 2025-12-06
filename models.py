from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, TIMESTAMP
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    max_simultaneous_vacations = Column(Integer, nullable=False)
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    login = Column(Text, unique=True, nullable=False)
    password = Column(Text, nullable=False)
    role = Column(Text, nullable=False)  # employee, manager, hr
    full_name = Column(Text, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'))
    manager_id = Column(String, ForeignKey('users.id'), nullable=True)

    department = relationship("Department", back_populates="users")
    manager = relationship("User", remote_side=[id])
    vacation_balances = relationship("VacationBalance", back_populates="user")
    vacation_requests = relationship("VacationRequest", back_populates="user")

class VacationBalance(Base):
    __tablename__ = 'vacation_balances'
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    year = Column(Integer, primary_key=True)
    total_days = Column(Integer, nullable=False)
    used_days = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="vacation_balances")

class VacationRequest(Base):
    __tablename__ = 'vacation_requests'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    comment = Column(Text)
    created_at = Column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates="vacation_requests")
    history = relationship("RequestHistory", back_populates="request")

class RequestHistory(Base):
    __tablename__ = 'request_history'
    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey('vacation_requests.id'))
    action = Column(Text, nullable=False)
    comment = Column(Text)
    acted_by = Column(String, ForeignKey('users.id'))
    acted_at = Column(TIMESTAMP, nullable=False)

    request = relationship("VacationRequest", back_populates="history")