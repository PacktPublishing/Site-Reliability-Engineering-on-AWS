#!/usr/bin/env python
# coding=utf-8

import logging
import psycopg2


#GlOBALS
MODULE = "postgres-helper"

# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def connect_to_db(dbconfig):
    try:
        conn = psycopg2.connect(**dbconfig)
    except (Exception, psycopg2.DatabaseError) as e:
        logging.error(f"connection error to {dbconfig['host']}:{dbconfig['database']} error {str(e)}")
        return
    else:
        logging.info(f"connected to {dbconfig['host']}:{dbconfig['database']}")
        return conn

def  get_db_version(conn):
    cur =conn.cursor()
    try:
        cur.execute('SELECT version()')
    except (Exception, psycopg2.DatabaseError) as e:
        logging.error(f"execution error {str(e)}")
        return
    else:
        db_version = cur.fetchone()
        logging.info(f"db versions {db_version}")
        cur.close()
        return db_version

def  init_db(conn,schema_file):
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(open(schema_file, "r").read())
    except Exception as e:
        logging.error(f"initdb execution error {str(e)}")
        return
    else:
        logging.info(f"tables created")
        cur.close()
        return

def update_car_availbility(conn,reg_id,status):
    updated_rows = 0
    sql = f"UPDATE car_availability set available = {status}  WHERE car_id = '{reg_id}'"
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        conn.rollback()
        logging.error(f" update availability execution error {str(e)}")
        raise Exception(f'update car availability error with {str(e)}')
        return
    else:
        updated_rows = cur.rowcount
        conn.commit()
    finally:
        cur.close()
        return updated_rows

def update_car(conn,car_det):
    updated_rows = 0
    sql = f"UPDATE cars set make = '{car_det[1]}' , model = '{car_det[2]}' , colour = '{car_det[3]}', capacity ='{car_det[4]}' WHERE number_plate = '{car_det[0]}'"
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        conn.rollback()
        logging.error(f" update execution error {str(e)}")
        raise Exception(f'update car error with {str(e)}')
        return
    else:
        updated_rows = cur.rowcount
        conn.commit()
    finally:
        cur.close()
        return updated_rows

def add_new_car(conn, car_det):
    sql = f"INSERT INTO cars VALUES('{car_det[0]}','{car_det[1]}','{car_det[2]}','{car_det[3]}','{car_det[4]}');"
    logging.debug(f"running sql {sql}")
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        conn.rollback()
        logging.debug(f"db:add car execution error 1 {str(e)}")
        raise Exception(f'add car error with {str(e)}')
    else:
        sql = f"INSERT INTO car_availability (car_id, available) VALUES('{car_det[0]}','true');"
        logging.info(f"running sql {sql}")
        try:
            cur.execute(sql)
        except Exception as e:
            conn.rollback()
            logging.debug(f"add car availability execution error 1 {str(e)}")
            raise Exception(f'add car availabilty error with {str(e)}')
        else:
            logging.info(f"updated car_availability")
            logging.info(f"last notice {str(conn.notices)}")
        conn.commit()
        cur.close()

def get_car(conn, reg_id):
    results = {}
    sql = f"SELECT * FROM cars WHERE number_plate = '{reg_id}';"
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        logging.debug(f"get car execution error {str(e)}")
        raise Exception(f'get car error with {str(e)}')
        return
    else:
        car_records = cur.fetchall()
        for row in car_records:
            results[row[0]] = {"make":row[1],"model":row[2],"colour":row[3],"capacity":row[4]}
    finally:
        cur.close()
        return results


def get_available_cars(conn):
    results = {}
    free_list = []
    sql = f"SELECT car_id FROM car_availability WHERE available = TRUE ;"
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        logging.debug(f"get car availability execution error {str(e)}")
        raise Exception(f'get car availability error with {str(e)}')
        return
    else:
        car_records = cur.fetchall()
        for row in car_records:
            free_list.append(row[0])
    finally:
        results['result'] = free_list
        cur.close()
        return results

def get_cars(conn):
    results = {}
    sql = f"SELECT number_plate FROM cars;"
    cur = conn.cursor()
    plate_list = []
    try:
        cur.execute(sql)
    except Exception as e:
        logging.error(f"execution error {str(e)}")
        raise Exception(f'error with {str(e)}')
        return
    else:
        car_records = cur.fetchall()
        for row in car_records:
            plate_list.append(row[0])
    finally:
        results['result'] = plate_list
        cur.close()
        return results

def add_booking(conn, booking_det):
    sql = f"INSERT INTO bookings (user_name,car_id,pickup,drop_off,booking_title,description) VALUES('{booking_det[0]}','{booking_det[1]}','{booking_det[2]}','{booking_det[3]}','{booking_det[4]}','{booking_det[5]}') RETURNING booking_id;"
    logging.info(f"running sql {sql}")
    cur = conn.cursor()
    id = None
    try:
        cur.execute(sql)
    except Exception as e:
        conn.rollback()
        logging.error(f"add booking execution error 1 {str(e)}")
        raise Exception(f'add booking error with {str(e)}')
    else:
        id = cur.fetchone()[0]
        conn.commit()
    finally:
        cur.close()
        return id

def get_bookings(conn):
    results = {}
    sql = f"SELECT booking_id,booking_title,user_name,approved,created,car_id FROM bookings ORDER by booking_id;"
    cur = conn.cursor()
    booking_list = []
    try:
        cur.execute(sql)
    except Exception as e:
        logging.error(f"execution error for booking list {str(e)}")
        raise Exception(f'error with booking list: {str(e)}')
        return
    else:
        booking_records = cur.fetchall()
        for row in booking_records:
            booking_list.append({"id":row[0],"title":row[1],"raised_by":row[2],"approved":row[3],"created":str(row[4]),"car-registration":str(row[5])})
    finally:
        results['result'] = booking_list
        cur.close()
        return results

def get_booking(conn,current_booking_id):
    results = {}
    sql = f"SELECT booking_id,booking_title,user_name,approved,created,car_id FROM bookings WHERE booking_id = {current_booking_id};"
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        logging.error(f"execution error for booking list {str(e)}")
        raise Exception(f'error with booking list: {str(e)}')
        return
    else:
        booking_records = cur.fetchall()
        for row in booking_records:
            results[row[0]] = {"title":row[1],"raised_by":row[2],"approved":row[3],"created":str(row[4]),"car-registration":str(row[5])}
    finally:
        cur.close()
        return results

def approve_booking(conn,working_booking_id):
    sql = f"UPDATE bookings SET approved = 'true' WHERE booking_id = {working_booking_id} RETURNING car_id,drop_off;"
    logging.debug(f"running sql {sql}")
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as e:
        conn.rollback()
        logging.debug(f"failed to approved booking {working_booking_id} {str(e)}")
        raise Exception(f'approval booking error with {str(e)}')
    else:
        row  = id = cur.fetchone()
        sql = f"UPDATE car_availability SET available = 'false', expires = '{row[1]}' WHERE car_id = '{row[0]}';"
        logging.info(f"running sql {sql}")
        try:
            cur.execute(sql)
        except Exception as e:
            conn.rollback()
            logging.debug(f"update car availability execution error 1 {str(e)}")
            raise Exception(f'update car availability error with {str(e)}')
        conn.commit()
        cur.close()




