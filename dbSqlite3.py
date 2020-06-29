# -*- coding: utf-8 -*-
import sqlite3


# 建立数据库连接
def OpenDb():
    database = "./data.db"
    conn = sqlite3.connect(database)
    # conn.row_factory = sqlite3.Row
    return conn


# 获取数据库连接
def GetSql(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    fields = []
    for field in cur.description:
        fields.append(field[0])

    result = cur.fetchall()
    # for item in result:
    #     print(item)
    cur.close()
    return result, fields


# 关闭数据库连接
def CloseDb(conn):
    conn.close()


# 获取数据库连接
def GetSql2(sql):
    conn = OpenDb()
    result, fields = GetSql(conn, sql)
    CloseDb(conn)
    return result, fields


# 改
def UpdateData(data, tablename):
    conn = OpenDb()
    values = []
    cursor = conn.cursor()
    idName1 = list(data)[0]
    idName2 = list(data)[1]
    for v in list(data)[2:]:
        values.append("%s='%s'" % (v, data[v]))
    sql = "update %s set %s where %s='%s' and %s='%s'" % (
    tablename, ",".join(values), idName1, data[idName1], idName2, data[idName2])
    # print (sql)
    cursor.execute(sql)
    conn.commit()
    CloseDb(conn)


# 增
def InsertData(data, tablename):
    conn = OpenDb()
    values = []
    cusor = conn.cursor()
    fieldNames = list(data)
    for v in fieldNames:
        values.append(data[v])
    sql = "insert into  %s (%s) values( %s) " % (tablename, ",".join(fieldNames), ",".join(["?"] * len(fieldNames)))
    # print(sql)
    cusor.execute(sql, values)
    conn.commit()
    CloseDb(conn)


# 删
def DelDataById(id1, id2, value1, value2, tablename):
    conn = OpenDb()
    # values = []
    cursor = conn.cursor()

    sql = "delete from %s  where %s=? and %s=?" % (tablename, id1, id2)
    # print (sql)

    cursor.execute(sql, (value1, value2))
    conn.commit()
    CloseDb(conn)
