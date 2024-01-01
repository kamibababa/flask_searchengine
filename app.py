from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from elasticsearch import Elasticsearch
from datetime import datetime
app = Flask(__name__)
CORS(app)
PAGE_SIZE = 8
client = Elasticsearch(hosts=['http://localhost:9200'])
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    key_words = request.values.get('q', 'python')                        # 获取到请求词
    page = request.values.get('p', '1')                            # 获取访问页码
    try:
        page = int(page)
    except:
        page = 1

    # page = 1
    query = {"bool": {"should": [{"match": {"title": key_words}}, {"match": {"description": key_words}}]}}
    start_time = datetime.now()  # 获取当前时间
    response = client.search(  # 原生的elasticsearch接口的search()方法，就是搜索，可以支持原生elasticsearch语句查询
        index="cnblogs",  # 设置索引名称
        # doc_type="doc",  # 设置表名称
        query=query,
        _source=["title", "description", "riqi", "url"],
        from_=(page - 1) * PAGE_SIZE,  # 从第几条开始获取
        size=PAGE_SIZE,  # 获取多少条数据
        highlight={  # 查询关键词高亮处理
            "pre_tags": ['<span class="keyWord">'],  # 高亮开始标签
            "post_tags": ['</span>'],  # 高亮结束标签
            "fields": {  # 高亮设置
                "title": {},  # 高亮字段
                "description": {}  # 高亮字段
            }
        }
    )
    total_nums = response["hits"]["total"]["value"]  # 获取查询结果的总条数
    if (page % PAGE_SIZE) > 0:  # 计算页数
        page_nums = int(total_nums / PAGE_SIZE) + 1
    else:
        page_nums = int(total_nums / PAGE_SIZE)
    hit_list = []  # 设置一个列表来储存搜索到的信息，返回给html页面
    for hit in response["hits"]["hits"]:  # 循环查询到的结果
        hit_dict = {}  # 设置一个字典来储存循环结果
        if "title" in hit["highlight"]:  # 判断title字段，如果高亮字段有类容
            hit_dict["title"] = "".join(hit["highlight"]["title"])  # 获取高亮里的title
        else:
            hit_dict["title"] = hit["_source"]["title"]  # 否则获取不是高亮里的title

        if "description" in hit["highlight"]:  # 判断description字段，如果高亮字段有类容
            hit_dict["description"] = "".join(hit["highlight"]["description"])[:500]  # 获取高亮里的description
        else:
            hit_dict["description"] = hit["_source"]["description"]  # 否则获取不是高亮里的description

        hit_dict["url"] = hit["_source"]["url"]  # 获取返回url
        hit_dict["create_date"] = hit["_source"]["riqi"]
        hit_dict["score"] = hit["_score"]
        hit_dict["source_site"] = "博客园"
        hit_dict["id"] = hit["_id"]
        hit_list.append(hit_dict)  # 将获取到内容的字典，添加到列表
    print(hit_list)
    end_time = datetime.now()  # 获取当前时间
    last_time = (end_time - start_time).total_seconds()
    obj = {"page": page,  # 当前页码
         "total_nums": total_nums,  # 数据总条数
         "all_hits": hit_list,  # 数据列表
         "key_words": key_words,  # 搜索词
         "page_nums": page_nums,  # 页数
         "page_szie": PAGE_SIZE,  # 页数
         "last_time": last_time  # 搜索时间
     }
    # 前后端分离调用此行
    # return jsonify(obj)
    # 前后端不分离调用此行
    return render_template('result.html',  **obj)

if __name__ == '__main__':
    app.run(debug=True)