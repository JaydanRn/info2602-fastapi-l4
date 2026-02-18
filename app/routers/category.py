from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

category_router = APIRouter(tags=["Category Management"])

@category_router.post("/category", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category_data: CategoryCreate, user: AuthDep, db: SessionDep):
    try:
        new_category = Category(
            user_id = user.id,
            text = category_data.text
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return new_category
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating a category",
        )
    
@category_router.post("/todo/{todo_id}/category/{cat_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
def add_category_to_todo(todo_id: int, cat_id: int, user: AuthDep, db: SessionDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not todo or not category:
        raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Unauthorized"
          )
    todo.categories.append(category)
    try:
        db.add(todo)
        db.commit()
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while assigning a category to a todo",
        )
    
@category_router.delete("/todo/{todo_id}/category/{cat_id}", status_code=status.HTTP_200_OK)
def remove_category_from_todo(todo_id: int, cat_id: int,  user: AuthDep, db: SessionDep):
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not todo or not category:
        raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Unauthorized"
          )
    if category not in todo.categories:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Category does not correspond to todo"
        )
    try:
        todo.categories.remove(category)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while removing a category from a todo",
        )
    
@category_router.get("/category/{cat_id}/todos", response_model=list[TodoResponse])
def get_todos_by_category(cat_id: int, user: AuthDep, db: SessionDep):
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
          raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Unauthorized"
          )
    return category.todos