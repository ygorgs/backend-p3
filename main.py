# coding: utf-8
#!/usr/bin/env python

from __future__ import unicode_literals

## standard library imports
import os
import datetime
import json

## app engine imports
import webapp2
import jinja2
from google.appengine.ext import ndb

## Instanciação do singleton do JINJA_ENVIRONMENT. 
## Pra quem não lembra, Jinja é o sistema de templates
## (server-side) que usaremos. Observe que aqui defino
## as strings que delimitam variáveis de forma que não
## se confundam com as strings usadas nos templates
## client-side do AngularJS.
JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True,
    variable_start_string = '{(',
    variable_end_string = ')}'
)

#NDB Models
class Comment(ndb.Model):
	bookid = ndb.StringProperty()
	name = ndb.StringProperty()
	text = ndb.StringProperty()

	def to_dict(self, URLBASE=""):
		data = super(Comment, self).to_dict()
		data["url"] = "%s/book/%s/comment" % (URLBASE, self.bookid)

class Book(ndb.Model):
	bookid = ndb.StringProperty()
	title = ndb.StringProperty()
	autors = ndb.StringProperty(repeated=True)
	description = ndb.TextProperty(default="sem descrição.")
	imageUrl = ndb.StringProperty()
	price = ndb.FloatProperty()
	comments = ndb.StructuredProperty(Comment)

	def to_dict(self, URLBASE=""):
		data = super(Book, self).to_dict()
		data["url"] = "%s/book/%s" % (URLBASE, self.bookid)
		return data

#Support Functions

def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()

    return obj

def data2json(data):
    return json.dumps(
        data,
        default=date_handler,
        indent=2,
        separators=(',', ': '),
        ensure_ascii=False
    )



class MainHandler(webapp2.RequestHandler):

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('doc.html')
        self.response.write(template.render())

class BooksCollectionHandler(webapp2.RequestHandler):

	# GET /book
	def get(self):
		books = Book.query()
		URLBASE = self.request.host_url
		data = []
		for book in books:
			data.append({"url": "$s/book/$s" % (URLBASE, book.bookid)})

		if(data == []):
			self.response.set_status(400)
			self.response.write('{"msg":"Nenhum livro encontrado", "error":404, "datetime":"%s"}' % (datetime.datetime.now().isoformat()))
           	return

		self.response.write(data2json(data).encode('utf-8'))

	#POST /book
	def post(self):
			book_data = json.loads(self.request.body)
			bookid = book_data.get('id')
			if(bookid is None):
				self.response.set_status(400)
				self.response.write('{"msg":"Campo obrigatório \'bookid\' não encontrado.", "error":400, "datetime":"%s"}' % (datetime.datetime.now().isoformat()))
				return

			#create
			book = Book(id=bookid)
			book.bookid = bookid
			book.title = book_data.get('title')
			book.autors = book_data.get('autors')
			book.description = book_data.get('description')
			book.imageUrl = book_data.get('imageUrl')
			book.price = book_data.get('price')
			book.put()

			#response
			URLBASE = self.request.host_url
			book_data['url'] = "%s/book/%s" % (URLBASE, book.bookid)
			self.response.headers[str("Location")] = str(book_data['url'])
			self.response.write(data2json(book_data).encode('utf-8'))
			self.response.set_status(201)




class BookHandler(webapp2.RequestHandler):

	#GET /book/:bookid
	def get(self, bookid):
		book = Book.get_by_id(bookid)
		if(book is None):
			self.response.set_status(400)
			self.response.write('{"msg":"Livro \'%s\' não encontrado", "error":404, "datetime":"%s"}' % (bookid, datetime.datetime.now().isoformat()))
           	return

		URLBASE = self.request.host_url
		self.response.write(data2json(book.to_dict(URLBASE)).encode('utf-8'))

	#PUT /book/:bookid
	def put(self, bookid):
		book = Book.get_by_id(bookid)
		if(book == None):
			book = Book(id=bookid)

		data = json.loads(self.request.body)
		book.bookid = bookid
		book.title = data['title']
		book.autors = data['autors']
		book.description = data['description']
		book.imageUrl = data['imageUrl']
		book.price = data['price']
		book.put()

		self.response.write(data2json(book.to_dict()).encode('utf-8'))

class CommentHandler(webapp2.RequestHandler):

	#GET /book/:bookid/comment
	def get(self, bookid):
		book = Book.get_by_id(bookid)
		if(book is None):
			self.response.set_status(400)
			self.response.write('{"msg":"Livro \'%s\' não encontrado", "error":404, "datetime":"%s"}' % (bookid, datetime.datetime.now().isoformat()))
           	return

		comments = book.get('comments')
		URLBASE = self.request.host_url
		self.response.write(data2json(comments.to_dict(URLBASE)).encode('utf-8'))

	#POST /book/:bookid/comment
	def post(self):
		comment_data = json.loads(self.request.body)
		bookid = comment_data.get('id')
		book = Book.get_by_id(bookid)

		data = json.loads(self.request.body)
		book.comments += data['comment']

		self.response.write(data2json(book.get('comments').to_dict()).encode('utf-8'))



app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/book', BooksCollectionHandler),
    ('/book/(.*)', BookHandler),
    ('/book/(.*)/comment', CommentHandler),
], debug=True)