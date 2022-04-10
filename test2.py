import argparse

import os
import sys

# def decorator(f):
#     def wraps(*args):
#         print(f"Calling function '{f.__name__}'")
#         return f(args)
#     return wraps

# thisdict = {
#   "brand": "Ford",
#   "electric": False,
#   "year": 1964,
#   "colors": {"a":"red", "b": "white", "c":"blue"}
# }
# a = {"tab1":{"a":"red"}}
# b = {"tab2":{"b":"red1"}}
# c = {"tab3":{"c":"red2"}}


# mm =[a,b,c]
# def print2():
#     newlist = findinlist("tab3",mm)
#     print(f"--- {newlist}")
#     for m in mm:
#         if "tab3" in m:
#             print(m)
def main():
    # Create the parser
    my_parser = argparse.ArgumentParser(description='List the content of a folder',allow_abbrev=True)

    # Add the arguments
    my_parser.add_argument('Path',
                        metavar='path',
                        type=str,
                        help='the path to list')
    my_parser.add_argument('-l',
                        '--long',
                        action='store_true',
                        help='enable the long listing format')

    # Execute parse_args()
    args = my_parser.parse_args()

    input_path = args.Path

    if not os.path.isdir(input_path):
        print('The path specified does not exist')
        sys.exit()

    for line in os.listdir(input_path):
        if args.long:  # Simplified long listing
            size = os.stat(os.path.join(input_path, line)).st_size
            line = '%10d  %s' % (size, line)
        print(line)



if __name__ == "__main__":
   main()