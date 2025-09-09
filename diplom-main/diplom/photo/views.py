from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from rest_framework.response import Response

from .permissions import IsOwnerOrReadOnly
from .models import Comment, Like, Post
from .serializers import CommentSerializers, PostSerializers


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializers
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializers
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        post_id = self.kwargs['post_pk']
        post = get_object_or_404(Post, pk=post_id)
        serializer.save(user=self.request.user, post=post)


class LikeView(APIView):
    permission_classes = [IsAuthenticated]

    def _update_likes_count(self, post):
        return post.like.count()

    def post(self, request, post_pk):
        post = get_object_or_404(Post, id=post_pk)
        user = request.user
        if Like.objects.filter(post=post, user=user).exists():
            return Response(
                {"error": "Вы уже поставили лайк этому посту"}
            )
        Like.objects.create(post=post, user=user)
        post.refresh_from_db()
        return Response({
            "status": "success",
            "like_count": self._update_likes_count(post)
        })

    def delete(self, request, post_pk):
        post = get_object_or_404(Post, id=post_pk)
        user = request.user
        like = get_object_or_404(Like, post=post, user=user)
        like.delete()
        post.refresh_from_db()
        return Response({
            "status": "success",
            "like_count": self._update_likes_count(post)
        })
