from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

todo_router = APIRouter(tags=["Todo Management"])

@todo_router.get("/todos", response_model=list[TodoResponse])
def get_todos(db: SessionDep, user:AuthDep):
    return user.todos

@todo_router.get("/todo/{id}", response_model=TodoResponse)
def get_todo_by_id(id :int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
                raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return todo

@todo_router.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo_data: TodoCreate, user: AuthDep, db: SessionDep):
    try:
        new_todo = Todo(
            user_id = user.id,
            text = todo_data.text
        )
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        return new_todo
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating an item",
        )
    
@todo_router.put("/todo/{id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
def update_todo(id: int, new_todo_data: TodoUpdate, user: AuthDep, db: SessionDep):
     todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
     if not todo:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
     if new_todo_data.text is not None:
        todo.text = new_todo_data.text        
     if new_todo_data.done is not None:
        todo.done = new_todo_data.done
     try:
        db.add(todo)
        db.commit()
        return todo
     except Exception:
          raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while updating an item",
        )
     
@todo_router.delete("/todo/{id}", status_code=status.HTTP_200_OK)
def delete_todo(id: int, user: AuthDep, db: SessionDep):
     todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
     if not todo:
          raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Unauthorized"
          )
     try:
        db.delete(todo)
        db.commit()
     except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )