from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, constr, validator
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from data_base import db_auth_utils as db



class MDPInvalide(Exception):
    pass 
#exception levée si :
#mdp<8 pas de maj, pas de chiffre


def MDP_valide(mdp):
    if len(mdp) <8 :
        raise MDPInvalide
    maj=[c for c in mdp if c.isupper()]
    numb=[c for c in mdp if c.isdigit()]

    if len(maj)<1 or len(numb)<1 :
        raise MDPInvalide
    

def get_username () :
    user = input("username : ")
    try :
        db.test_username(user)
    except db.UsernameExistsError as e :
        print(f"Erreur : {e}")
        return get_username()
    return user

def get_mail ():
    mail=input("mail :")
    try :
        db.test_email(mail)
    except db.EmailExistsError as m :
        print (f"Erreur : {m}")
        return get_mail()
    return mail

def get_mdp ():
    mdp=input("mot de passe :")
    try :
        MDP_valide(mdp)
    except MDPInvalide :
        print("Le mot de passe doit respecter les conditions")
        return get_mdp()
    return mdp

def Sign_up():
    user=get_username()
    mail=get_mail()
    mdp=get_mdp()
    db.add_user(user,mail,mdp)
    

Sign_up()