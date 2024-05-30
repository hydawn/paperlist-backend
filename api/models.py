import base64

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TypedModel(models.Model):
    objects: models.Manager

    class Meta:
        abstract = True


class Paper(TypedModel):
    # created by this user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=4096)
    # linked to Author by PaperToAuthor
    abstract = models.CharField(max_length=0x20000)
    file_name = models.CharField(max_length=1024)
    file_content = models.FileField(upload_to='objects/')
    publication_date = models.DateField()
    journal = models.CharField(max_length=1024)
    total_citations = models.IntegerField(validators=[MinValueValidator(0, message='citations must be at least 0')])
    private = models.BooleanField(default=False)

    @property
    def detail_json(self):
        with open(self.file_content.name, 'rb') as file:
            file_content = base64.b64encode(file.read()).decode('utf-8')
        return {
                'paperid': str(self.id),
                'userid': str(self.user.id),
                'username': self.user.username,
                'title': self.title,
                'abstract': self.abstract,
                'file_name': self.file_name,
                'file_content': file_content,
                'publication_date': str(self.publication_date),
                'journal': self.journal,
                'total_citations': self.total_citations,
                'is_private': self.private,
                }

    @property
    def simple_json(self):
        return {
                'paperid': str(self.id),
                'userid': str(self.user.id),
                'username': self.user.username,
                'title': self.title,
                'publication_date': str(self.publication_date),
                'journal': self.journal,
                'total_citations': self.total_citations,
                'is_private': self.private,
                }


#class Scholar(TypedModel):
#    name = models.CharField(max_length=1024)
#    email = models.CharField(max_length=1024)


class PaperByScholar(TypedModel):
    ''' paper created by scholar '''
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    scholar = models.CharField(max_length=256)
    # scholar = models.ForeignKey(Scholar, on_delete=models.CASCADE)
    # 1st, or comu...
    # scholar_role = models.CharField(max_length=256)


class PaperCited(TypedModel):
    ''' the cite_paper cites paper '''
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='cited_by')
    cite_paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='cites')


class PaperSet(TypedModel):
    # created by this user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, null=True)
    private = models.BooleanField(default=False)
    # tags = models.CharField(max_length=4096, null=True)


class PaperSetContent(TypedModel):
    ''' the content of paper set '''
    paper_set = models.ForeignKey(PaperSet, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)


class PaperTextComments(TypedModel):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    # commented by user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=4096)


class PaperStarComments(TypedModel):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    # commented by user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # from 1 to 5
    star = models.IntegerField(
            validators=[
                MinValueValidator(1, message='stars must be at least 1'),
                MaxValueValidator(5, message='stars cannot be more than 5')
            ]
        )


#class PaperSetComments(TypedModel):
#    paper_set = models.ForeignKey(Paper, on_delete=models.CASCADE)
#    # commented by user
#    user = models.ForeignKey(User, on_delete=models.CASCADE)
#    comment = models.CharField(max_length=4096)


# # TODO: maybe I should use a privilaged user to manage papertags
# # and after that, paper tags can have description
# class PaperTags(TypedModel):
#     tag_name = models.CharField(max_length=128)
#     # tag_description = models.CharField(max_length=1024)
#
#
# class PaperWithTag(TypedModel):
#     paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
#     tag = models.ForeignKey(PaperTags, on_delete=models.CASCADE)
#
#
# class PaperSetWithTag(TypedModel):
#     paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
#     tag = models.ForeignKey(PaperTags, on_delete=models.CASCADE)
