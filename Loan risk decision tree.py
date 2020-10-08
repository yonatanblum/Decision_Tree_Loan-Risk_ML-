import glob
import numpy as np
import pandas as pd

import os

os.environ['PATH'] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin'

from graphviz import Digraph

train_file_name = "train.txt"
val_file_name = "val.txt"
test_file_name = "test.txt"


# this function return dictionary of 10 feature and 1 class G / B
def read_data_from_file(filename):
    f = open(filename, "r")
    d = list()
    for line in f:
        head = line[0:1]
        if head not in ['%', '/', ' ', '#']:
            line = line[:-1]
            x = line.split(',')
            d.append(x)
    return d


# Column labels.
# These are used only to print the tree.
header = ["A1: Checking status", "A2: Saving status", "A3: Credit history", 'A4: Housing', 'A5: Job',
          'A6: Property magnitude', 'A7: Number of dependents', 'A8: Number of existing credits',
          'A9: Own telephones or not', 'A10: Foreign workers or not', 'Result']


def unique_vals(rows, col):
    """Find the unique values for a column in a dataset."""
    return set([row[col] for row in rows])


def class_counts(rows):
    """Counts the number of each type of example in a dataset."""
    counts = {}  # a dictionary of label -> count.
    for row in rows:
        # in our dataset format, the label is always the last column
        label = row[-1]
        if label not in counts:
            counts[label] = 0
        counts[label] += 1
    return counts


def is_numeric(value):
    """Test if a value is numeric."""
    return isinstance(value, int) or isinstance(value, float)


class Question:
    """A Question is used to partition a dataset.

    This class just records a 'column number' (e.g., 0 for Checking status) and a
    'column value' (e.g., x). The 'match' method is used to compare
    the feature value in an example to the feature value stored in the
    question.
    """

    def __init__(self, column, value):
        self.column = column
        self.value = value

    def match(self, example):
        # Compare the feature value in an example to the
        # feature value in this question.
        val = example[self.column]
        if is_numeric(val):
            return val >= self.value
        else:
            return val == self.value

    def r_header(self):
        return header[self.column]

    def __repr__(self):
        # This is just a helper method to print
        # the question in a readable format.
        condition = "=="
        if is_numeric(self.value):
            condition = ">="
        return "Is %s %s %s?" % (
            header[self.column], condition, str(self.value))


def partition(rows, question):
    """Partitions a dataset.

    For each row in the dataset, check if it matches the question. If
    so, add it to 'true rows', otherwise, add it to 'false rows'.
    """
    true_rows, false_rows = [], []
    for row in rows:
        if question.match(row):
            true_rows.append(row)
        else:
            false_rows.append(row)
    return true_rows, false_rows


def gini(rows):
    """Calculate the Gini Impurity for a list of rows.
    """
    counts = class_counts(rows)
    impurity = 1
    # print(counts)
    for lbl in counts:
        '''lbl=key , counts = dict()'''
        ''' G=1-E(1->n)[Pk^2]=1-E(k=1->n)[mk/m]^2'''
        prob_of_lbl = counts[lbl] / float(len(rows))
        impurity -= prob_of_lbl ** 2
    return impurity


def info_gain(left, right, current_uncertainty):
    """Information Gain.

    The uncertainty of the starting node, minus the weighted impurity of
    two child nodes.
    """
    p = float(len(left)) / (len(left) + len(right))
    return current_uncertainty - p * gini(left) - (1 - p) * gini(right)


def find_best_split(rows):
    """Find the best question to ask by iterating over every feature / value
    and calculating the information gain."""
    best_gain = 0  # keep track of the best information gain
    best_question = None  # keep train of the feature / value that produced it
    current_uncertainty = gini(rows)
    n_features = len(rows[0]) - 1  # number of columns

    for col in range(n_features):  # for each feature

        values = set([row[col] for row in rows])  # unique values in the column

        for val in values:  # for each value

            question = Question(col, val)

            # try splitting the dataset
            true_rows, false_rows = partition(rows, question)

            # Skip this split if it doesn't divide the
            # dataset.
            if len(true_rows) == 0 or len(false_rows) == 0:
                continue

            # Calculate the information gain from this split
            gain = info_gain(true_rows, false_rows, current_uncertainty)

            # You actually can use '>' instead of '>=' here
            # but I wanted the tree to look a certain way for our
            # toy dataset.
            if gain >= best_gain:
                best_gain, best_question = gain, question

    return best_gain, best_question


class Leaf:
    """A Leaf node classifies data.

    This holds a dictionary of class  -> number of times
    it appears in the rows from the training data that reach this leaf.
    """

    def __init__(self, rows):
        self.predictions = class_counts(rows)

    def p_question(self):
        x = list(self.predictions.keys())
        return x[0]


class Decision_Node:
    """A Decision Node asks a question.

    This holds a reference to the question, and to the two child nodes.
    """

    def __init__(self,
                 question,
                 true_branch,
                 false_branch):
        self.question = question
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.gain = 0
        self.gini = 1

    def p_question(self):
        return self.question

    def update_gain(self, gain=0, gini=1):
        self.gain = gain
        self.gini = gini


def decision_tree_build(rows):
    # Try partitioing the dataset on each of the unique attribute,
    # calculate the information gain,
    # and return the question that produces the highest gain.
    gain, question = find_best_split(rows)
    gini_val = gini(rows)
    # Base case: no further info gain
    # Since we can ask no further questions,
    # we'll return a leaf.
    if gain == 0:
        return Leaf(rows)

    # If we reach here, we have found a useful feature / value
    # to partition on.
    true_rows, false_rows = partition(rows, question)

    # Recursively build the true branch.
    true_branch = decision_tree_build(true_rows)

    # Recursively build the false branch.
    false_branch = decision_tree_build(false_rows)

    # Return a Question node.
    # This records the best feature / value to ask at this point,
    # as well as the branches to follow
    # dependingo on the answer.
    x = Decision_Node(question, true_branch, false_branch)
    x.update_gain(gain, gini_val)
    return x


def print_tree(node, spacing=""):
    """World's most elegant tree printing function."""
    # Base case: we've reached a leaf
    if isinstance(node, Leaf):
        print(spacing + "Predict", node.predictions)
        return

    # Print the question at this node
    print(spacing + str(node.question))

    # Call this function recursively on the true branch
    print(spacing + '--> True:')

    print_tree(node.true_branch, spacing + "  ")

    #     # Call this function recursively on the false branch
    print(spacing + '--> False:')
    print_tree(node.false_branch, spacing + "  ")


def classify(row, node):
    """See the 'rules of recursion' above."""

    # Base case: we've reached a leaf
    if isinstance(node, Leaf):
        return node.predictions

    # Decide whether to follow the true-branch or the false-branch.
    # Compare the feature / value stored in the node,
    # to the example we're considering.
    if node.question.match(row):
        return classify(row, node.true_branch)
    else:
        return classify(row, node.false_branch)


def print_leaf(counts):
    """A nicer way to print the predictions at a leaf."""
    total = sum(counts.values()) * 1.0
    probs = {}
    for lbl in counts.keys():
        probs[lbl] = str(int(counts[lbl] / total * 100)) + "%"
    return probs


def visualize_tree(tree):
    def add_nodes_edges(tree, dot=None):
        # Create Digraph object
        if dot is None:
            dot = Digraph()
            dot.node(name=str(tree), label=str(tree.p_question()))
        if isinstance(tree, Leaf):
            dot.node(name=str(tree), label=str(tree.p_question()))
        else:
            # Add nodes
            if tree.false_branch:
                dot.node(name=str(tree.false_branch),
                         label=str(str(tree.false_branch.p_question()) + '\nIG = ' + str(tree.gain) + '\nGini = ' + str(
                             tree.gini)))
                dot.edge(str(tree), str(tree.false_branch),label='False')
                dot = add_nodes_edges(tree.false_branch, dot=dot)

            if tree.true_branch:
                dot.node(name=str(tree.true_branch),
                         label=str(str(tree.true_branch.p_question()) + '\nIG = ' + str(tree.gain) + '\nGini = ' + str(
                             tree.gini)))
                dot.edge(str(tree), str(tree.true_branch),label='True')
                dot = add_nodes_edges(tree.true_branch, dot=dot)

        return dot

    # Add nodes recursively and create a list of edges
    dot = add_nodes_edges(tree)

    return dot


def print_accuracy(test_data, my_tree):
    tG = 0
    tB = 0
    f = 0

    for row in test_data:
        print("Actual: %s. Predicted: %s" %
              (row[-1], print_leaf(classify(row, my_tree))))
        x = classify(row, my_tree)
        x = list(x.keys())
        if x[0] == 'G' and row[-1] == 'G':
            tG += 1
        elif x[0] == 'B' and row[-1] == 'B':
            tB += 1
        else:
            f += 1
    print("tG = " + str(tG) + " tB = " + str(tB) + " false = " + str(f) + " Classification Accuracy is  : " + str(
            ((tG + tB) / (tG + tB + f)) * 100) + "%")


# '''-------------------------------------------------------'''


train_data = read_data_from_file(train_file_name)
val_data = read_data_from_file(val_file_name)
test_data = read_data_from_file(test_file_name)

my_tree = decision_tree_build(train_data)
# print_tree(my_tree)

print_accuracy(test_data, my_tree)
dot = visualize_tree(my_tree)

dot.render('/test-output/EX4.gv', view=True)
