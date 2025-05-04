from django.urls import path, include
from . import views
from django.views.generic import DetailView, ListView
from .models import Tag


app_name = "fts_app"
urlpatterns = [
    # path("", views.IndexView.as_view(), name="index"),
    # path('tag/<int:pk>/', DetailView.as_view(model=Tag, template_name="fts_app/tag.html"), name='tag'),
    # path('listtag/', ListView.as_view(model=Tag, template_name="fts_app/listtag.html"), name='listtag'),

    # jwt
    path('', views.Home.as_view(), name="index"),

]