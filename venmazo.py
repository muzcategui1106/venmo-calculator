# venmaso.py
import os
import sys
import json
import copy
from collections import defaultdict


venmo_info = ""
sub_total = 0
tax = 0
tip = 0
total = 0

def get_venmo_info():
    with open("{}/{}".format(os.getcwd(),"venmaso.json"), 'r') as f:
        file_info = f.read()
    return json.loads(file_info)

def gather_venmo_basic_info(venmo_info):
    global sub_total
    global tax
    global tip
    global total
    sub_total = venmo_info["subTotal"]
    tax_raw = venmo_info["tax"]
    tip_raw = venmo_info["tip"]

    # calculate tax and tip
    tax = float(tax_raw  / sub_total)
    tip = float(tip_raw  / (sub_total + tax_raw))
    total = float(sub_total + tax_raw + tip_raw)

    # check that all items listed in json match for sub_total
    check_sub_total(venmo_info, sub_total)

def check_sub_total(venmo_info, subtotal):
    global sub_total
    check_sub_total = 0
    for item in venmo_info["items"].values():
        check_sub_total += item[1]
    if sub_total != check_sub_total:
        print("Items missing in list. Idiot dont screw yourself over")
        print("Sub total should be {} and you got {}".format(sub_total, check_sub_total))
    return

def calculate_per_person_price(venmo_info):
    global sub_total
    global tax
    global tip

    # get total of items, this will be useful for validation
    item_quantity = defaultdict(lambda : {})
    for key in venmo_info["items"]:
        item_quantity[key]["quantity"] = venmo_info["items"][key][0]
        item_quantity[key]["price"] = venmo_info["items"][key][1]
        item_quantity[key]["remaining"] = venmo_info["items"][key][0]

    # start calculatin per person
    # very crappy approach to do this but I dont care :)
    people = copy.deepcopy(venmo_info["people"])
    people2 = copy.deepcopy(people)
    for person in people:
        total = 0
        for key in people[person].keys():
            # make sure item exists in list and if it does then add to total
            if not key in item_quantity:
                print("Item {} for person {} does not exist in list of items {}".format(key, person, item_quantity.keys()))
                sys.exit(1)
            item_total = (people[person][key] *  item_quantity[key]["price"]) / item_quantity[key]["quantity"]
            total += item_total
            people2[person][key] = {}
            people2[person][key]["quantity"] = people[person][key]
            people2[person][key]["price"] = item_total

            # for verification subtratc to the remaining field on item_quantity[key]["remaining"]
            item_quantity[key]["remaining"] -= people[person][key]

        person_sub_total = total
        total += total * tax
        total += total * tip
        people2[person]["estimates"] = {}
        people2[person]["estimates"]["sub_total"] = person_sub_total
        people2[person]["estimates"]["tax"] = person_sub_total * tax
        people2[person]["estimates"]["tip"] = ((person_sub_total * tax) + person_sub_total)  * tip
        people2[person]["estimates"]["total"] = total
        people2[person]["estimates"]["total"] = total

    people = people2

    # do validation that no items are remaining and that total is correct
    check_venmo_totals(people, item_quantity)

    return people


def check_venmo_totals(people, item_quantity):
    global total

    # check all items have been accounted for
    for key in item_quantity:
        quantity = item_quantity[key]["remaining"]
        if  quantity != 0:
            print("Somebody has not paid for his/her {}  we have {} unnacounted for... Make them pay".format(key, quantity))
            sys.exit(1)

    total_calculated = 0
    for person in people.keys():
        total_calculated += people[person]["estimates"]["total"]
        print("Person: {} Total {}".format(person ,people[person]["estimates"]["total"]))

    print("total {} ... calculated total {}".format(total, total_calculated))
    under = int(total_calculated) < int(total)
    over = int(total_calculated) > int(total)
    if under :
        print("You are loosing exactly {} ... Did you forget to include items".format((int(total_calculated - total))))
    elif over:
        print("You are gaining ${} out of this WTF take out items".format((int(total_calculated - total))))


def get_totals_into_file(people):
    for person in people:
        with open("{}/{}.json".format(os.getcwd(), person), 'w') as f:
            json.dump(people[person], f)


def main():
    venmo_info = get_venmo_info()
    gather_venmo_basic_info(venmo_info)
    people = calculate_per_person_price(venmo_info)
    get_totals_into_file(people)



if __name__ == "__main__":
    main()