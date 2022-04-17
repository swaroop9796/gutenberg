import json
import logging.config

from flask import Flask, jsonify, request

from db_handler import DBHandler
from parameter_table_mapping import parameter_table_mapping
from util import get_exception_details

app = Flask(__name__)
LOG = logging.getLogger(__name__)


def log_startup_info():
    LOG.info('Starting Data Extractor program')


def setup_logging(logging_conf):
    logging.config.dictConfig(logging_conf)
    return


@app.route('/get_book_details', methods=['GET'])
def get_book_details():
    try:
        gutenberg_id = request.args.get('book_id')
        language = request.args.get('language')
        mime_type = request.args.get('mime_type')
        topic = request.args.get('topic')
        author = request.args.get('author')
        title = request.args.get('title')
        parameters = {"gutenberg_id": gutenberg_id, "language": language, "mime_type": mime_type, "topic": topic,
                      "author": author,
                      "title": title}
        non_null_parameters = {k: v for k, v in parameters.items() if v is not None}
        db_result = fetch_book_details_from_db(non_null_parameters)
        json_result = None
        if db_result:
            json_result = convert_db_result_to_json(db_result)
        if json_result:
            return jsonify(json_result), 200
        else:
            return jsonify({}), 200
    except Exception as e:
        return jsonify({"error": "Internal server error. Once please check parameters' spellings or URL syntax"}), 501
        LOG.error(get_exception_details(e))


def convert_db_result_to_json(db_result):
    json_result = {"no_of_book": 0, "book_list": []}
    temp_result_dict = {}
    for book_object in db_result:
        if book_object[0] in temp_result_dict.keys():
            temp_result_dict[book_object[0]]["subjects"].append(book_object[6]) if book_object[6] not in temp_result_dict[book_object[0]]["subjects"] else temp_result_dict[book_object[0]]["subjects"]
            temp_result_dict[book_object[0]]["bookshelves"].append(book_object[7]) if book_object[7] not in temp_result_dict[book_object[0]]["bookshelves"] else temp_result_dict[book_object[0]]["bookshelves"]
            temp_result_dict[book_object[0]]["URLs"].append(book_object[8]) if book_object[8] not in temp_result_dict[book_object[0]]["URLs"] else temp_result_dict[book_object[0]]["URLs"]
        else:
            temp_dict = {}
            temp_dict["book_title"] = book_object[1]
            temp_dict["author_name"] = book_object[2]
            temp_dict["author_birth_year"] = book_object[3]
            temp_dict["author_death_year"] = book_object[4]
            temp_dict["language"] = book_object[5]
            temp_dict["subjects"] = [book_object[6]]
            temp_dict["bookshelves"] = [book_object[7]]
            temp_dict["URLs"] = [book_object[8]]
            temp_result_dict[book_object[0]] = temp_dict
    json_result["no_of_book"] = len(temp_result_dict)
    json_result["book_list"] = list(temp_result_dict.values())
    return json_result




def fetch_book_details_from_db(non_null_parameters):
    if "gutenberg_id" in non_null_parameters:
        if "," in non_null_parameters["gutenberg_id"]:
            value_list = [x.strip() for x in non_null_parameters["gutenberg_id"].split(',')]
            temp_string = " bb.gutenberg_id IN ("
            for index, value in enumerate(value_list):
                if index != len(value_list) - 1:
                    temp_string += value + ","
                else:
                    temp_string += value + ") ORDER BY bb.download_count DESC;"
        else:
            temp_string = " bb.gutenberg_id = " + non_null_parameters[
                "gutenberg_id"] + " ORDER BY bb.download_count DESC;"
    #TODO improvment:  Use ORM instead of query
        query = '''SELECT bb.gutenberg_id ,bb.title, ba.name AS Author_name, ba.birth_year AS Author_birth_year, ba.death_year AS Author_death_year,
                bl.code AS Language, bs.name AS Subject, bb2.name AS Bookshelf, bf.url AS URL
                FROM books_book bb
                LEFT JOIN books_book_authors bba ON bb.id = bba.book_id
                LEFT JOIN books_author ba ON ba.id = bba.author_id
                LEFT JOIN books_book_languages bbl ON bbl.book_id = bb.id
                LEFT JOIN books_language bl ON bl.id = bbl.language_id
                LEFT JOIN books_book_subjects bbs ON bbs.book_id = bb.id
                LEFT JOIN books_subject bs ON bs.id = bbs.subject_id
                LEFT JOIN books_book_bookshelves bbb ON bbb.book_id = bb.id
                LEFT JOIN books_bookshelf bb2 ON bb2.id = bbb.bookshelf_id
                LEFT JOIN books_format bf ON bf.book_id = bb.id
                WHERE''' + temp_string
    else:
        temp_string = ""
        for key, value in non_null_parameters.items():
            if key != "gutenberg_id":
                if key == "topic":
                    temp_string += "("
                    for item in parameter_table_mapping[key]:
                        temp_string += "("
                        if "," in value:
                            value_list = [x.strip() for x in value.split(',')]
                            temp_string += " (" + item + " LIKE"
                            for index, value1 in enumerate(value_list):
                                if index != len(value_list) - 1:
                                    temp_string += " '" + value1 + "%' OR " + item + " LIKE"
                                else:
                                    temp_string += " '" + value1 + "%')"
                        else:
                            temp_string += " " + item + " LIKE " + "'" + value + "%'"
                        temp_string += ")OR"
                    if temp_string[-2:] == "OR":
                        temp_string = temp_string[:-2]
                    temp_string += ")"
                else:
                    if "," in value:
                        value_list = [x.strip() for x in value.split(',')]
                        temp_string += " " + parameter_table_mapping[key] + " IN ("
                        for index, value1 in enumerate(value_list):
                            if index != len(value_list) - 1:
                                temp_string += "'" + value1 + "'" + ","
                            else:
                                temp_string += "'" + value1 + "'" + ")"
                    else:
                        temp_string += " " + parameter_table_mapping[key] + "=" + '"' + value + '"'
            temp_string += " AND"
        if temp_string[-4:] == " AND":
            temp_string = temp_string[:-4]
        temp_string += " ORDER BY bb.download_count DESC;"
        query = '''SELECT bb.gutenberg_id, bb.title, ba.name AS Author_name, ba.birth_year AS Author_birth_year, ba.death_year AS Author_death_year,
                        bl.code AS Language, bs.name AS Subject, bb2.name AS Bookshelf, bf.url AS URL
                        FROM books_book bb
                        LEFT JOIN books_book_authors bba ON bb.id = bba.book_id
                        LEFT JOIN books_author ba ON ba.id = bba.author_id
                        LEFT JOIN books_book_languages bbl ON bbl.book_id = bb.id
                        LEFT JOIN books_language bl ON bl.id = bbl.language_id
                        LEFT JOIN books_book_subjects bbs ON bbs.book_id = bb.id
                        LEFT JOIN books_subject bs ON bs.id = bbs.subject_id
                        LEFT JOIN books_book_bookshelves bbb ON bbb.book_id = bb.id
                        LEFT JOIN books_bookshelf bb2 ON bb2.id = bbb.bookshelf_id
                        LEFT JOIN books_format bf ON bf.book_id = bb.id
                        WHERE''' + temp_string
    db = DBHandler(program_config["mysql_db"])
    result = db.execute_query(query)
    return result


def main():
    try:
        setup_logging(program_config['logging'])
        log_startup_info()
        app.run(debug=True)
    except Exception as e:
        LOG.error(get_exception_details)


if __name__ == "__main__":
    with open('config.json', 'r') as f:
        program_config = json.load(f)
    main()
