import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, make_transient
from marshmallow import fields, ValidationError
from flask_marshmallow import Marshmallow
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')
app.json.sort_keys = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)


class Watchlist(Base):
    __tablename__ = "Watchlist"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    overview: Mapped[str] = mapped_column(db.String(200))
    genres: Mapped[str] = mapped_column(db.String(200))
    popularity: Mapped[int] = mapped_column(db.Integer())
    release_date: Mapped[str] = mapped_column(db.String(200))
    poster_path: Mapped[str] = mapped_column(db.String(200))
    review: Mapped[str] = mapped_column(db.String(200), nullable=True)
    
    
    
with app.app_context():
    db.create_all()
    
    
class WatchListSchema(ma.Schema):
    id = fields.Integer(required=False)
    original_title = fields.String(required=True)
    overview = fields.String(required=True)
    genres = fields.String(required=True)
    popularity = fields.Integer(required=True)
    release_date = fields.String(required=True)
    poster_path = fields.String(required=True)
    review = fields.String(required=False)

    class Meta:
        fields = ("id", "original_title", "overview", "genres", "popularity", "release_date", "poster_path", "review")
        
watchlist_schema = WatchListSchema()
watchlists_schema = WatchListSchema(many=True)


@app.route("/watchlist", methods = ["GET"])
def get_watchlist():
    query = select(Watchlist) #Selects data from our Customer Table
    result = db.session.execute(query).scalars()
    watchlist = result.all()

    return watchlists_schema.jsonify(watchlist)


@app.route("/watchlist", methods=["POST"])
def add_to_watchlist():
    try:
        watchlist_data = watchlist_schema.load(request.json)
        print(watchlist_data)

    except ValidationError as err:
        print(err.messages)
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        new_watchlist = Watchlist(original_title=watchlist_data['original_title'], overview=watchlist_data["overview"][:200], 
                                  genres=watchlist_data["genres"], popularity=watchlist_data["popularity"],
                                  release_date=watchlist_data["release_date"], poster_path=watchlist_data["poster_path"], review="")
        session.add(new_watchlist)
        session.commit()
    
    return jsonify({"message": "New movie added to Watch List succesfully"}), 201


@app.route("/watchlist/<int:id>", methods=["PUT"])
def update_watchlist(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Watchlist).filter(Watchlist.id==id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"error": "Customer Not Found"}), 404
            watchlist = result
            watchlist_data = {
                "id": result.id,
                "original_title": result.original_title,
                "overview": result.overview,
                "genres": result.genres,
                "popularity": result.popularity,
                "release_date": result.release_date,
                "poster_path": result.poster_path,
                "review": result.review
            }
            try:
                watchlist_data = watchlist_schema.load(watchlist_data)
            except ValidationError as err:
                print(err.messages)
                return jsonify(err.messages), 400
            
            for field, value in request.json.items():
                setattr(watchlist, field, value)
                
            
            session.commit()
    return jsonify({"message": "Customer details updated succesfully"}), 200



if __name__ == "__main__":
    app.run(debug=True)