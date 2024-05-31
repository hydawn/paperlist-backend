import base64
import fitz  # PyMuPDF

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint


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
    def file_bytes(self):
        with open(self.file_content.name, 'rb') as file:
            return file.read()

    @property
    def file_bytes_base64(self):
        return base64.b64encode(self.file_bytes).decode('utf-8')

    def file_bytes_preview(self, num_pages: int = 1):
        document = fitz.open(self.file_content.name)
        new_pdf = fitz.open()
        for page_num in range(min(num_pages, len(document))):
            new_pdf.insert_pdf(document, from_page=page_num, to_page=page_num)
        pdf_bytes = new_pdf.tobytes()
        new_pdf.close()
        document.close()
        return pdf_bytes

    @property
    def full_json(self):
        return {
                'paperid': str(self.id),
                'userid': str(self.user.id),
                'username': self.user.username,
                'title': self.title,
                'abstract': self.abstract,
                'file_name': self.file_name,
                'file_content': self.file_bytes_base64,
                'publication_date': str(self.publication_date),
                'journal': self.journal,
                'total_citations': self.total_citations,
                'is_private': self.private,
                'authors': [i.scholar for i in PaperByScholar.objects.filter(paper=self)]
                }


    @property
    def simple_json(self):
        return {
                'paperid': str(self.id),
                'userid': str(self.user.id),
                'username': self.user.username,
                'title': self.title,
                'abstract': self.abstract,
                'publication_date': str(self.publication_date),
                'journal': self.journal,
                'total_citations': self.total_citations,
                'is_private': self.private,
                'authors': [i.scholar for i in PaperByScholar.objects.filter(paper=self)]
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

    class Meta:
        constraints = [
            UniqueConstraint(fields=['paper', 'cite_paper'], name='unique_paper_cites')
        ]



class PaperSet(TypedModel):
    # created by this user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, null=True)
    private = models.BooleanField(default=False)
    # tags = models.CharField(max_length=4096, null=True)

    @property
    def json(self):
        return {
                'userid': str(self.user.id),
                'username': self.user.username,
                'name': self.name,
                'description': self.description,
                'private': self.private
                }


class PaperSetContent(TypedModel):
    ''' the content of paper set '''
    paper_set = models.ForeignKey(PaperSet, on_delete=models.CASCADE, related_name='has_paper')
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='in_paperset')

    class Meta:
        constraints = [
            UniqueConstraint(fields=['paper', 'paper_set'], name='unique_paper_in_sets')
        ]


class PaperTextComments(TypedModel):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    # commented by user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=4096)
    commented_on = models.DateTimeField(auto_now_add=True)

    @property
    def json(self):
        return {
                # 'paperid': str(self.paper.id),
                'userid': str(self.user.id),
                'username': self.user.username,
                'comment': self.comment,
                'commented_on': self.commented_on,
            }


class PaperStarComments(TypedModel):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    # commented by user
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # from 1 to 5
    star = models.IntegerField(
            validators=[
                MinValueValidator(1, message='stars must be at least 1'),
                MaxValueValidator(10, message='stars cannot be more than 10')
            ]
        )
    commented_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['paper', 'user'], name='unique_paper_user')
        ]

    @property
    def json(self):
        return {
                'paperid': str(self.paper.id),
                'userid': str(self.user.id),
                'username': self.user.username,
                'star': self.star,
            }




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
