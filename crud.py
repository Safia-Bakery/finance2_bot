from sqlalchemy.orm import Session
import models
import pytz
from typing import Optional
import requests
from sqlalchemy import or_,and_,Date,cast
from datetime import datetime 
timezonetash = pytz.timezone("Asia/Tashkent")


def get_user(db:Session,tg_id):
    query = db.query(models.Users).filter(models.Users.tg_id==tg_id).first()
    return query

def get_history(db:Session,user_id,order_id):
    query = db.query(models.History).filter(and_(models.History.user_id==user_id,models.History.order_id==order_id)).first()
    return query

def history_update(db:Session,history_id,status):
    query = db.query(models.History).filter(models.History.id==history_id).first()
    if query:
        query.status=status
        db.commit()
        db.refresh(query)
    return query


def get_sphere_user(db:Session,sphere_id,order_id):
    history_query = db.query(models.History).filter(models.History.order_id==order_id).all()
    exist_user_list = [i.user_id for i in history_query]
    query = db.query(models.SphereUsers).filter(and_(models.SphereUsers.sphere_id==sphere_id,~models.SphereUsers.user_id.in_(exist_user_list)))
    return query.order_by(models.SphereUsers.sequence.asc()).first()

def history_create(db:Session,user_id,order_id):
    query = models.History(user_id=user_id,order_id=order_id,status=0)
    db.add(query)
    db.commit()
    db.refresh(query)
    return query

def order_status_update(db:Session,order_id,status):
    query = db.query(models.Orders).filter(models.Orders.id==order_id).first()
    query.status=status
    db.commit()
    return True

def order_get_with_id(db:Session,order_id):
    query = db.query(models.Orders).filter(models.Orders.id==order_id).first()
    return query