from django import forms

from posts.models import Post, Group, Comment


def validate_not_empty(value):
    if not value:
        raise forms.ValidationError(
            'А кто поле будет заполнять, Пушкин?',
            params={'value': value},
        )


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    text = forms.CharField(widget=forms.Textarea,
                           validators=[validate_not_empty],
                           label='Текст поста',
                           help_text='Заполните текст поста')
    group = forms.ModelChoiceField(required=False,
                                   queryset=Group.objects.all(),
                                   label='Группа',
                                   help_text='Выберите группу')


class CommentForm(forms.ModelForm):
    class Meta():
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Напишите ваш комментарий',
        }
