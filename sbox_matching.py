import copy
import networkx as nx
from networkx.algorithms import bipartite
import random
import math
# import matplotlib.pyplot as plt

# GLOBAL
MEMO = []
MEMO_SIGNALS = []
MEMO_LOCAL = []

class Case:
    def __init__(self, members):
        self.members = self.generate_case(members)

    def generate_case(self, members):
        stripped_members = members.replace("(", "")
        stripped_members = stripped_members.replace(")", "")
        list_of_members = stripped_members.split(" ")
        # Remove empty strings
        list_of_members = [i for i in list_of_members if i]
        return list_of_members


class Gate:
    def __init__(self, name, num_inputs, evaulate_function, determine_input_groups=None, idx1=None, idx2=None, sbox_idx=None, term_idx=None):
        self.name = name
        self.num_inputs = num_inputs
        self.evaulate_function = evaulate_function
        self.determine_input_groups = determine_input_groups
        self.input_groups = {}
        self.input_groups_signals = {}
        self.subset = []
        self.idx1 = idx1
        self.idx2 = idx2
        self.sbox_idx = sbox_idx
        self.term_idx = term_idx
        self.is_main_term = False
        self.is_remainder_term = False
        self.Z_RAIL = 'No Z RAIL'
        self.Z_INDEX = 'No Z INDEX'

    def __str__(self):
        input_labels = []
        if(self.num_inputs == 2):
            input_labels = ["a", "b"]
        elif(self.num_inputs == 3):
            input_labels = ["a", "b", "c"]
        elif(self.num_inputs == 4):
            input_labels = ["a", "b", "c", "d"]

        z = f"z{self.sbox_idx}_{self.Z_RAIL}_"

        for label in input_labels:
            z = z + str(self.input_groups[label.lower()][0]) + "_"
        
        print(f"-- DEBUG : {z}")
        # TODO: Fix the issue Forest was talking about, it has to do with the z not including RAIL or other information in the MEMO list
        # Because of this, if a remainder is calculated in a different Z_INDEX, it will not recompte since it has the same 'z'

        z = z[:-1]
        if z in MEMO and not self.is_main_term:
            return ""
        else:
            MEMO.append(z)
            if not self.is_main_term and not self.is_remainder_term:
                MEMO_SIGNALS.append(z)

        if(self.is_remainder_term):
            instance_label =  "NET_" + \
                str(self.sbox_idx) + "_" + str(self.Z_INDEX) + "_" + self.Z_RAIL + "_REMAINDER_" + str(self.idx1)
            gate_label = instance_label + " : " + self.name + "m_a"
        elif(self.num_inputs == 4 and self.is_remainder_term):
            instance_label =  "NET_" + \
                str(self.sbox_idx) + "_" + str(self.Z_INDEX) + "_" + self.Z_RAIL + "_" + \
                str(self.idx1) + "_" + str(self.idx2)
            gate_label = instance_label + " : " + self.name + "m_a"
        else:
            instance_label = "NET_" + \
                str(self.sbox_idx) + "_" + str(self.term_idx) + "_" + str(self.Z_INDEX) + "_" + str(self.Z_RAIL) + "_" + str(self.name) + "_"
            for label in input_labels:
                instance_label = instance_label + \
                    str('_'.join(self.input_groups[label.lower()])) + "_"
            instance_label = instance_label[:-1]
            gate_label = instance_label + " : " + self.name + "m_a"

            matching = ''.join(instance_label.split("_")[2:])

        print(gate_label)
        print("port map (")

        for label in input_labels:
            if(len(self.input_groups[label.lower()]) > 1):
                print("\t" + label + " => z" + str(self.sbox_idx) + "_" +
                      str('_'.join(self.input_groups[label.lower()])) + ",")
            else:
                # Evens are RAIL0
                # Odds are RAIL1
                term = list(self.input_groups[label.lower()][0])
                RAIL = "RAIL1" if term[2] == "1" else "RAIL0"
                idx = (self.sbox_idx * 6) + int(term[1])
                INDEX = int(idx)

                print(f"\t{label} => B({INDEX}).{RAIL},")


        # z = z[:-1]
        # MEMO_SIGNALS.append(z)

        print(f"\ts => SLEEP_{self.sbox_idx},")

        if(self.is_main_term or self.is_remainder_term):
            z_idx = self.sbox_idx * 4 + self.Z_INDEX
            # print(f"\tz => Z({z_idx}).{self.Z_RAIL}")
            OR_NET = f"OR_NET_{self.sbox_idx}_{self.Z_INDEX}_{self.Z_RAIL}({self.term_idx})"
            # MEMO_SIGNALS.append(OR_NET)
            print(f"\tz => {OR_NET}")
        else:
            print(f"\tz => {z}")
        print(");")


        return ""

    def evaluate(self, pair):
        return self.evaulate_function(pair)

    def find_input_groups(self, pair):
        self.input_groups = self.determine_input_groups(pair)

    def get_input_group_signals(self):
        input_labels = []
        if(self.num_inputs == 2):
            input_labels = ["a", "b"]
        elif(self.num_inputs == 3):
            input_labels = ["a", "b", "c"]
        elif(self.num_inputs == 4):
            input_labels = ["a", "b", "c", "d"]

        # Create the z signal
        z = f"z{self.sbox_idx}_"
        for label in input_labels:
            z = z + str(self.input_groups[label.lower()][0]) + "_"
        z = z[:-1]

        for label in input_labels:
            if(len(self.input_groups[label.lower()]) > 1):
                combined_net = str('_'.join(self.input_groups[label.lower()]))
                primary_net = f"z{str(self.sbox_idx)}_{combined_net},"
                self.input_groups_signals[label] = primary_net
            else:
                # Evens are RAIL0
                # Odds are RAIL1
                term = list(self.input_groups[label.lower()][0])
                RAIL = "RAIL1" if term[2] == "1" else "RAIL0"
                idx = (self.sbox_idx * 6) + int(term[1])
                INDEX = int(idx)

                primary_net = f"B({INDEX}).{RAIL},"
                self.input_groups_signals[label] = primary_net

        self.input_groups_signals['s'] = f'SLEEP_{self.sbox_idx}'
        
        if(self.is_main_term or self.is_remainder_term):
            self.input_groups_signals['z'] = f'q_{self.sbox_idx}_{self.Z_INDEX}_{self.Z_RAIL}'
        else:
            self.input_groups_signals['z'] = f'q_{self.sbox_idx}_{self.Z_INDEX}_{self.Z_RAIL}'
            


def th54w32_evaluate(pair):
    if(len(pair.matches) >= 2):
        return True
    else:
        return False

def th54w32_evaluate_input_groups(pair):
    input_groups = {
        "a": [],
        "b": [],
        "c": [],
        "d": [],
    }

    all_inputs = []
    all_inputs.extend(pair.case1.members)
    all_inputs.extend(pair.case2.members)
    all_inputs = list(set(all_inputs))
    included_inputs = []
    remaining_inputs = all_inputs
    # print(f"All inputs : {all_inputs}")
    # print(f"Case 1 : {pair.case1.members}")
    # print(f"Case 2 : {pair.case2.members}")

    case1_remaining_inputs = copy.deepcopy(pair.case1.members)
    case2_remaining_inputs = copy.deepcopy(pair.case2.members)
    
    # print(f"Case 1 remaining inputs : {case1_remaining_inputs}")
    # print(f"Case 2 remaining inputs : {case2_remaining_inputs}")

    a_input = pair.matches
    for a in a_input:
        remaining_inputs.remove(a)
        case1_remaining_inputs.remove(a)
        case2_remaining_inputs.remove(a)
    included_inputs.extend(pair.matches)

    # print(f"A: {a_input}")
    # print(f"Included inputs A: {included_inputs}")
    # print(f"Remaining inputs A: {remaining_inputs}")
    # print()
    # num_inputs_b = 0
    # if len(remaining_inputs) == 7 or len(remaining_inputs) == 8:
    #     num_inputs_b = 4
    # elif len(remaining_inputs) == 6:
    #     num_inputs_b = 3
    # elif len(remaining_inputs) == 5:
    #     num_inputs_b = 2
    # elif len(remaining_inputs) == 4:
    #     num_inputs_b = 1

    # print(f"Num inputs B: {num_inputs_b}")
    b_input = case1_remaining_inputs
    included_inputs.extend(b_input)
    for b in b_input:
        remaining_inputs.remove(b)
    
    # print(f"B: {b_input}")
    # print(f"Included inputs B: {included_inputs}")
    # print(f"Remaining inputs B: {remaining_inputs}")
    # print()

    c_input = []
    if len(remaining_inputs) == 4:
        c_input = remaining_inputs[0:3]
    elif len(remaining_inputs) == 3:
        c_input = remaining_inputs[0:2]
    elif len(remaining_inputs) == 2:
        c_input = remaining_inputs[0:1]
    included_inputs.extend(c_input)
    for c in c_input:
        remaining_inputs.remove(c)
    
    # print(f"C: {c_input}")
    # print(f"Included inputs C: {included_inputs}")
    # print(f"Remaining inputs C: {remaining_inputs}")
    # print()
    
    
    d_input = remaining_inputs[0:1]
    included_inputs.extend(d_input)
    for d in d_input:
        remaining_inputs.remove(d)
    
    # print(f"D: {d_input}")
    # print(f"Included inputs D: {included_inputs}")
    # print(f"Remaining inputs D: {remaining_inputs}")
    # print()
    
    input_groups["a"].extend(a_input)
    input_groups["b"].extend(b_input)
    input_groups["c"].extend(c_input)
    input_groups["d"].extend(d_input)

    # print(f"Input groups : {input_groups}")

    return input_groups


def thxor0_evaluate(pair):
    if(len(pair.remainders_case1) == 2 and len(pair.remainders_case2) == 2):
        return True
    else:
        return False


def thxor0_evaluate_input_groups(pair):
    input_groups = {
        "a": [],
        "b": [],
        "c": [],
        "d": [],
    }
    input_groups["a"].append(pair.remainders_case1[0])
    input_groups["b"].append(pair.remainders_case1[1])
    input_groups["c"].append(pair.remainders_case2[0])
    input_groups["d"].append(pair.remainders_case2[1])

    return input_groups


def th12_evaluate(pair):
    pass
    return False


def th12_evaluate_input_groups(pair):
    pass
    return False


def th22_evaluate(pair):
    pass
    return False


def th22_evaluate_input_groups(pair_subset):
    input_groups = {
        "a": [],
        "b": [],
    }
    input_groups["a"].append(pair_subset[0])
    input_groups["b"].append(pair_subset[1])

    return input_groups

def th13_evaluate(pair):
    pass
    return False


def th13_evaluate_input_groups(pair):
    pass
    return False


def th33_evaluate(pair):
    pass
    return False


def th33_evaluate_input_groups(pair_subset):
    input_groups = {
        "a": [],
        "b": [],
        "c": [],
    }
    input_groups["a"].append(pair_subset[0])
    input_groups["b"].append(pair_subset[1])
    input_groups["c"].append(pair_subset[2])

    return input_groups

def th14_evaluate(pair):
    pass
    return False


def th14_evaluate_input_groups(pair):
    pass
    return False

def th44_evaluate(pair):
    pass
    return False


def th44_evaluate_input_groups(pair_subset):
    input_groups = {
        "a": [],
        "b": [],
        "c": [],
        "d": [],
    }
    input_groups["a"].append(pair_subset[0])
    input_groups["b"].append(pair_subset[1])
    input_groups["c"].append(pair_subset[2])
    input_groups["d"].append(pair_subset[3])

    return input_groups


th54w32 = Gate("th54w32", 4, th54w32_evaluate, th54w32_evaluate_input_groups)
thxor0 = Gate("thxor0", 4, thxor0_evaluate, thxor0_evaluate_input_groups)
th12 = Gate("th12", 2, th12_evaluate, th12_evaluate_input_groups)
th22 = Gate("th22", 2, th22_evaluate, th22_evaluate_input_groups)
th13 = Gate("th13", 3, th13_evaluate, th13_evaluate_input_groups)
th33 = Gate("th33", 3, th33_evaluate, th33_evaluate_input_groups)
th14 = Gate("th14", 4, th14_evaluate, th14_evaluate_input_groups)
th44 = Gate("th44", 4, th44_evaluate, th44_evaluate_input_groups)



gates = [th54w32]


class Pair:
    def __init__(self, case1, c1idx, case2, c2idx):
        self.case1 = case1
        self.case1_index = c1idx
        self.case2 = case2
        self.case2_index = c2idx
        self.matches = []
        self.remainders = []
        self.remainders_case1 = []
        self.remainders_case2 = []
        self.gates = []

    def __str__(self):
        print(f"Case 1 - idx {self.case1_index}: {str(self.case1.members)}")
        print(f"Case 2 - idx {self.case2_index}: {str(self.case2.members)}")
        print("Matches: " + str(self.matches))
        # print("Remainders: " + str(self.remainders))
        print("Remainders Case1: " + str(self.remainders_case1))
        print("Remainders Case2: " + str(self.remainders_case2))
        return ""

    def find_matches(self):
        for mem in self.case1.members:
            if mem in self.case2.members and mem not in self.matches:
                self.matches.append(mem)
        self.find_remainders()

    def find_remainders(self):
        for mem in self.case1.members:
            if mem not in self.matches:
                self.remainders.append(mem)
                self.remainders_case1.append(mem)
        for mem in self.case2.members:
            if mem not in self.matches:
                self.remainders.append(mem)
                self.remainders_case2.append(mem)


class MatchController:
    def __init__(self, sbox_index):
        self.sbox_index = sbox_index
        self.case_list = []
        self.pairs = []
        # Remainders are cases with another pair that don't have enough matches
        self.remainders = []

    def set_RAIL(self, RAIL):
        self.Z_RAIL = RAIL

    def set_Z_INDEX(self, Z_INDEX):
        self.Z_INDEX = Z_INDEX

    def generate_case_list(self, z):
        cases = z.split("+")
        for case in cases:
            if(case.count(" ") > 8):
                self.case_list.append(Case(case))
            else:
                self.remainders.append(Case(case))

    def generate_pairs(self):
        for i in range(0, len(self.case_list)):
            for j in range(i+1, len(self.case_list)):
                case1 = self.case_list[i]
                case2 = self.case_list[j]
                if(case1 != case2):
                    self.pairs.append(Pair(case1, i, case2, j))

    def find_matches(self):
        for pair in self.pairs:
            pair.find_matches()

    def drop_bad_matches(self, threshold):
        temp_remainders = []
        for pair in self.pairs:
            if len(pair.matches) < threshold:
                temp_remainders.append(pair)
                self.remainders.append(pair.case1)
                self.remainders.append(pair.case2)
            if len(pair.matches) > 3:
                temp_remainders.append(pair)

        for r in temp_remainders:
            self.pairs.remove(r)

    def filter_remainders(self):
        self.remainders = list(set(self.remainders))
        loop_remainders = copy.copy(self.remainders)
        for remainder in loop_remainders:
            for pair in self.pairs:
                if remainder.members == pair.case1.members:
                    if remainder in self.remainders:
                        self.remainders.remove(remainder)
                        break
                elif remainder.members == pair.case2.members:
                    if remainder in self.remainders:
                        self.remainders.remove(remainder)
                        break

    def set_gates(self, gates):
        for i in range(len(self.pairs)):
            for gate in gates:
                if gate.evaluate(self.pairs[i]) and gate not in self.pairs[i].gates:
                    term_idx = i
                    g = copy.deepcopy(gate)
                    g.idx1 = self.pairs[i].case1_index
                    g.idx2 = self.pairs[i].case2_index
                    g.sbox_idx = self.sbox_index
                    g.term_idx = term_idx
                    g.is_main_term = True
                    g.Z_RAIL = self.Z_RAIL
                    g.Z_INDEX = self.Z_INDEX
                    self.pairs[i].gates.append(g)

    def set_input_groups(self):
        # Get input groups
        for pair in self.pairs:
            for gate in pair.gates:
                gate.find_input_groups(pair)
                # Get input group signals
                gate.get_input_group_signals()

    def set_input_groups_subset(self):
        for pair in self.pairs:
            for gate in pair.gates:
                if(gate.name == 'th54w32'):
                    th22_1 = copy.deepcopy(th22)
                    th22_2 = copy.deepcopy(th22)
                    th22_3 = copy.deepcopy(th22)
                    th33_1 = copy.deepcopy(th33)
                    th33_2 = copy.deepcopy(th33)
                    th33_3 = copy.deepcopy(th33)
                    th44_1 = copy.deepcopy(th44)
                    th44_2 = copy.deepcopy(th44)
                    th44_3 = copy.deepcopy(th44)

                    th22_1.sbox_idx = self.sbox_index
                    th22_2.sbox_idx = self.sbox_index
                    th22_3.sbox_idx = self.sbox_index
                    th33_1.sbox_idx = self.sbox_index
                    th33_2.sbox_idx = self.sbox_index
                    th33_3.sbox_idx = self.sbox_index
                    th44_1.sbox_idx = self.sbox_index
                    th44_2.sbox_idx = self.sbox_index
                    th44_3.sbox_idx = self.sbox_index

                    th22_1.Z_INDEX = self.Z_INDEX
                    th22_2.Z_INDEX = self.Z_INDEX
                    th22_3.Z_INDEX = self.Z_INDEX
                    th33_1.Z_INDEX = self.Z_INDEX
                    th33_2.Z_INDEX = self.Z_INDEX
                    th33_3.Z_INDEX = self.Z_INDEX
                    th44_1.Z_INDEX = self.Z_INDEX
                    th44_2.Z_INDEX = self.Z_INDEX
                    th44_3.Z_INDEX = self.Z_INDEX

                    th22_1.Z_RAIL = self.Z_RAIL
                    th22_2.Z_RAIL = self.Z_RAIL
                    th22_3.Z_RAIL = self.Z_RAIL
                    th33_1.Z_RAIL = self.Z_RAIL
                    th33_2.Z_RAIL = self.Z_RAIL
                    th33_3.Z_RAIL = self.Z_RAIL
                    th44_1.Z_RAIL = self.Z_RAIL
                    th44_2.Z_RAIL = self.Z_RAIL
                    th44_3.Z_RAIL = self.Z_RAIL

                    # print(gate.input_groups)

                    # th22_1_subset = [
                    #     pair.case1.members[0], pair.case1.members[1]]
                    # th22_2_subset = [
                    #     pair.case2.members[0], pair.case2.members[1]]
                    # th22_3_subset = [
                    #     pair.case2.members[2], pair.case2.members[3]]
                    # th33_1_subset = [pair.case1.members[2],
                    #                  pair.case1.members[3], pair.case1.members[4]]

                    a_input = gate.input_groups['a']
                    b_input = gate.input_groups['b']
                    c_input = gate.input_groups['c']

                    # Generate A subset
                    if(len(a_input) == 4):
                        th44_1.find_input_groups(a_input)
                        gate.subset.append(th44_1)
                    elif(len(a_input) == 3):
                        th33_1.find_input_groups(a_input)
                        gate.subset.append(th33_1)
                    elif(len(a_input) == 2):
                        th22_1.find_input_groups(a_input)
                        gate.subset.append(th22_1)
                    
                    # Generate B subset
                    if(len(b_input) == 4):
                        th44_2.find_input_groups(b_input)
                        gate.subset.append(th44_2)
                    elif(len(b_input) == 3):
                        th33_2.find_input_groups(b_input)
                        gate.subset.append(th33_2)
                    elif(len(b_input) == 2):
                        th22_2.find_input_groups(b_input)
                        gate.subset.append(th22_2)
                    
                    # Generate C subset
                    if(len(c_input) == 3):
                        th33_3.find_input_groups(c_input)
                        gate.subset.append(th33_3)
                    elif(len(c_input) == 2):
                        th22_3.find_input_groups(c_input)
                        gate.subset.append(th22_3)
                    
                    # th22_1.find_input_groups(a_input)
                    # gate.subset.append(th22_1)

                    # if len(b_input) == 4:
                    #     th44_1.find_input_groups(b_input)
                    #     gate.subset.append(th44_1)
                    # elif len(b_input) == 3:
                    #     th33_1.find_input_groups(b_input)
                    #     gate.subset.append(th33_1)

                    # th22_2.find_input_groups(c_input)
                    # gate.subset.append(th22_2)

                    # th22_1.find_input_groups(th22_1_subset)
                    # th22_2.find_input_groups(th22_2_subset)
                    # th22_3.find_input_groups(th22_3_subset)
                    # th33_1.find_input_groups(th33_1_subset)

                    # gate.subset.append(th22_1)
                    # gate.subset.append(th22_2)
                    # gate.subset.append(th22_3)
                    # gate.subset.append(th33_1)

    def create_networkx_graph(self):
        self.G = nx.Graph()

        for pair in self.pairs:
            self.G.add_node(pair.case1_index)
            self.G.add_node(pair.case2_index)
            self.G.add_edge(pair.case1_index, pair.case2_index)

        # print("--- Networkx graph ---")
        # print(list(self.G.nodes))
        # print(list(self.G.edges))

    def create_bipartite_graph(self):

        # [0, 1, 2, 3, 4, 5]
        # [0, 1, 2] top_nodes
        # [3, 4, 5] bottom_nodes

        nodes = list(self.G.nodes)
        self.graph_nodes = nodes
        midpoint = int(len(nodes)//2)
        top_nodes = nodes[:midpoint]
        bottom_nodes = nodes[midpoint:]

        self.BG = nx.Graph()
        self.BG.add_nodes_from(top_nodes, bipartite=0)
        self.BG.add_nodes_from(bottom_nodes, bipartite=1)

        # Add edges only from a top node to a bottom node
        for edge in self.G.edges:
            if edge[0] in top_nodes and edge[1] in bottom_nodes:
                self.BG.add_edge(edge[0], edge[1])

        # print("--- Bipartite Graph ---")
        # print(list(self.BG.nodes))
        # print(list(self.BG.edges))

    def create_graph_matching(self):

        self.graph_matching_dict = bipartite.matching.hopcroft_karp_matching(
            self.BG)

        for node in self.graph_nodes:
            if node not in self.graph_matching_dict:
                for edge in self.G.edges:
                    if edge[0] == node:
                        self.graph_matching_dict[node] = edge[1]
                        break
                    elif edge[1] == node:
                        self.graph_matching_dict[node] = edge[0]
                        break

        self.num_matched_terms = math.ceil(len(self.graph_matching_dict) / 2)
        self.num_or_net = self.num_matched_terms + len(self.remainders)
        self.or_net_current_idx = 0

        print("--- Graph Matching ---")
        print("-- " + str(self.graph_matching_dict))
        print("-- Number of matches: " + str(len(self.graph_matching_dict)))
        print("-- Number of matched terms: " + str(self.num_matched_terms))

    def create_matching_pairs(self):
        self.matching_pairs = []
        for key, value in self.graph_matching_dict.items():
            if key < value:
                for pair in self.pairs:
                    if pair.case1_index == key and pair.case2_index == value and pair not in self.matching_pairs:
                        self.matching_pairs.append(pair)
                        break
            elif key > value:
                for pair in self.pairs:
                    if pair.case1_index == value and pair.case2_index == key and pair not in self.matching_pairs:
                        self.matching_pairs.append(pair)
                        break
                    
    def create_z_outputs(self):
        # Using the matching pairs and the remainders, create the Z outputs
        pass

    def or_tree(self, width):
        or_tree_gates = []

        for k in range(self.log_u(width, 4) - 1):
            # NOT LAST LEVEL
            if (self.level_number(width, k, 4) > 4):
                # PRINCIPLE
                for j in range((self.level_number(width, k , 4) / 4) - 1):
                    th14_1 = copy.deepcopy(th14)
                    th14_1.sbox_idx = self.sbox_index
                    th14_1.Z_INDEX = self.Z_INDEX
                    th14_1.determine_input_groups

                # LEFT OVER GATE
                if self.log_u((self.level_number(width, k, 4) / 4) + (self.level_number(width, k, 4) % 4), 4) + k + 1 != self.log_u(width, 4):
                    # NEED22
                    if (self.level_number(width, k, 4) % 4) == 2:
                        th12_1 = copy.deepcopy(th12)
                        th12_1.sbox_idx = self.sbox_index
                        th12_1.Z_INDEX = self.Z_INDEX
                        th12_1.determine_input_groups
                    # NEED33
                    elif (self.level_number(width, k, 4) % 4) == 3:
                        th13_1 = copy.deepcopy(th13)
                        th13_1.sbox_idx = self.sbox_index
                        th13_1.Z_INDEX = self.Z_INDEX
                        th13_1.determine_input_groups

                # LEFT OVER SIGNALS
                if (self.log_u((self.level_number(width, k, 4) / 4) + (self.level_number(width, k, 4) % 4), 4) + k + 1 == self.log_u(width, 4)) and ((self.level_number(width, k, 4) % 4) != 0):
                    # RENAME SIGNALS
                    pass

        # LAST12
        if self.level_number(width, k, 4) == 2:
            th12_1 = copy.deepcopy(th12)
            th12_1.sbox_idx = self.sbox_index
            th12_1.Z_INDEX = self.Z_INDEX
            th12_1.determine_input_groups

        # LAST13
        if self.level_number(width, k, 4) == 3:
            th13_1 = copy.deepcopy(th13)
            th13_1.sbox_idx = self.sbox_index
            th13_1.Z_INDEX = self.Z_INDEX
            th13_1.determine_input_groups

        # LAST14
        if self.level_number(width, k, 4) == 4:
            th14_1 = copy.deepcopy(th14)
            th14_1.sbox_idx = self.sbox_index
            th14_1.Z_INDEX = self.Z_INDEX
            th14_1.determine_input_groups

    def level_number(self, width, level, base):
        num = width
        if level != 0:
            for i in range(1, level):
                if (self.log_u((num / base) + (num % base), base) + i) == self.log_u(width, base):
                    num = (num / base) + (num % base)
                else:
                    num = (num / base) + 1
        return num
        
    def log_u(self, L, R):
        temp = 1
        level = 0
        if L == 1:
            return 0
        while temp < L:
            temp = temp * R
            level += 1

        return level

    def show_pairs(self):
        print("Pairs")
        for pair in self.pairs:
            print(pair)

    def show_remainders(self):
        print("---- Remainders ----")
        for remainder in self.remainders:
            print(str(remainder.members))

    def show_remainders_gates(self):
        for remainder in self.remainders:
            len_remainder = len(remainder.members)
            if(len_remainder == 4):
                term_idx = self.num_matched_terms + self.remainders.index(remainder)
                gate = copy.deepcopy(th44)
                gate.Z_INDEX = self.Z_INDEX
                gate.term_idx = term_idx
                # Get idx of the remainder in the list of cases
                gate.idx1 = self.remainders.index(remainder)
                input_set = [remainder.members[0], remainder.members[1],
                             remainder.members[2], remainder.members[3]]
            elif(len_remainder == 3):
                gate = copy.deepcopy(th33)
                input_set = [remainder.members[0],
                             remainder.members[1], remainder.members[2]]
            elif(len_remainder == 2):
                gate = copy.deepcopy(th22)
                input_set = [remainder.members[0], remainder.members[1]]
            gate.is_remainder_term = True
            gate.sbox_idx = self.sbox_index
            gate.Z_RAIL = self.Z_RAIL
            gate.Z_INDEX = self.Z_INDEX
            gate.find_input_groups(input_set)
            print("----Remainder Term----")
            print(gate)

    def show_or_tree_gate(self):
        gate_label = f"OR_{self.sbox_index}_{self.Z_INDEX}_{self.Z_RAIL} : ortreem"
        
        # Used for the output of the whole entity
        z_idx = self.sbox_index * 4 + self.Z_INDEX
        generic_width = self.num_matching_pairs + 1
        print(gate_label)
        print(f"generic map(width => {generic_width})")
        print(f"port map(")
        print(f"\ta => OR_NET_{self.sbox_index}_{self.Z_INDEX}_{RAIL},")
        print(f"\tsleep => SLEEP_{self.sbox_index},")
        print(f"\tko => Z({z_idx}).{self.Z_RAIL}")
        print(f");")

    def show_matched_gates(self):
        self.num_matching_pairs = len(self.matching_pairs) + len(self.remainders) - 1
        OR_SIGNAL = f"OR_NET_{self.sbox_index}_{self.Z_INDEX}_{self.Z_RAIL} : STD_LOGIC_VECTOR({self.num_matching_pairs} downto 0)"
        MEMO_SIGNALS.append(OR_SIGNAL)
        for i in range(len(self.matching_pairs)):
            for gate in self.matching_pairs[i].gates:
                gate.term_idx = i
                if gate.name == "thxor0":
                    continue
                print("----Main Term----")
                print("-- " + str(self.matching_pairs[i].case1.members))
                print("-- " + str(self.matching_pairs[i].case2.members))
                print(gate)
                if(len(gate.subset) > 0):
                    print("----Subsets----")
                    for subset in gate.subset:
                        print(subset)

    def show_signals(self):
        signals = list(dict.fromkeys(MEMO_SIGNALS))
        print("---- Signals ----")
        for signal in signals:
            if "downto" in signal:
                print(f"SIGNAL {signal};")
            else:
                print(f"SIGNAL {signal} : STD_LOGIC;")

    def show_statistics(self):
        num_terms = len(self.case_list)
        num_remainders = len(self.remainders)
        print(f"-- Number of Terms : {num_terms}")
        print(f"-- Number of Remainders : {num_remainders}")

    def show_documentation(self):
        print("\n--- Documentation ---")
        print("-- #How to read the graph matching")
        print("-- The graph matching is a dictionary with the keys being the top nodes and the values being the bottom nodes")
        print(
            "-- This is how the script matches up the terms in order to make a TH54W32 gate")
        print("-- #How to read the instance labels")
        print(
            "-- Main terms will have just NET{SBOX INDEX}_{FIRST TERM INDEX}_{SECOND TERM INDEX}\n")

    def show_gates(self):
        print()
        print("-------------- Gates --------------")
        num_gates = 0
        for p in self.pairs:
            if len(p.gates) > 0:
                num_gates += len(p.gates)
        print("Number Of Pairs: " + str(len(self.pairs)))
        print("Number Of Gates among all Pairs: " + str(num_gates))
        print()
        for pair in self.pairs:
            for gate in pair.gates:
                print("----Pair Indicies----")
                print("Case 1: " + str(pair.case1_index))
                print("Case 2: " + str(pair.case2_index))
                print("----Gate----")
                print(str(gate.name))
                print("----Case Terms----")
                print("Case 1: " + str(pair.case1.members))
                print("Case 2: " + str(pair.case2.members))
                print("----Input Terms----")
                print(str(gate.name) + " " + str(gate.input_groups))
                print("----Subsets----")
                for subset in gate.subset:
                    print(str(subset.name) + " " + str(subset.input_groups))
                print()


# SBOX 0
Z0_00 = "(B21  B51  B30  B40) + (B01  B11  B21  B51  B30) + (B01  B31  B41  B51  B10) + (B01  B31  B41  B51  B20) + (B11  B31  B41  B51  B00) + (B01  B11  B21  B30  B40) + (B01  B11  B51  B30  B40) + (B11  B31  B51  B00  B20) + (B01  B11  B21  B31  B41  B50) + (B10  B20  B40  B50) + (B01  B31  B10  B20  B40) + (B01  B31  B20  B40  B50) + (B01  B41  B10  B30  B50) + (B01  B41  B20  B30  B50) + (B11  B41  B00  B20  B30) + (B11  B41  B00  B30  B50) + (B21  B41  B00  B10  B50) + (B21  B51  B00  B10  B40) + (B11  B00  B20  B30  B50) + (B11  B21  B31  B00  B40  B50) + (B00  B10  B20  B30  B40)"
Z0_01 = "(B01  B21  B31  B40) + (B01  B11  B21  B31  B51) + (B31  B41  B20  B50) + (B41  B51  B00  B10) + (B41  B51  B10  B30) + (B01  B11  B31  B51  B40) + (B11  B21  B31  B51  B40) + (B21  B10  B40  B50) + (B41  B00  B10  B20) + (B01  B21  B31  B10  B50) + (B01  B41  B51  B20  B30) + (B11  B31  B41  B00  B50) + (B21  B41  B51  B00  B30) + (B01  B51  B10  B20  B30) + (B11  B31  B00  B20  B50) + (B31  B51  B00  B10  B20) + (B01  B11  B21  B41  B30  B50) + (B21  B00  B30  B40  B50) + (B01  B11  B20  B30  B40  B50) + (B11  B51  B00  B20  B30  B40)"
Z0_10 = "(B01  B11  B31  B41) + (B11  B21  B31  B41  B51) + (B11  B21  B40  B50) + (B31  B41  B20  B50) + (B11  B00  B30  B40) + (B01  B11  B51  B20  B40) + (B01  B21  B31  B40  B50) + (B01  B21  B51  B10  B40) + (B21  B41  B51  B00  B10) + (B11  B21  B00  B30  B50) + (B11  B51  B00  B20  B30) + (B31  B41  B00  B10  B50) + (B31  B51  B10  B20  B40) + (B21  B00  B30  B40  B50) + (B51  B00  B10  B20  B40) + (B01  B21  B41  B10  B30  B50) + (B01  B41  B51  B10  B20  B30) + (B01  B10  B20  B30  B40  B50)"
Z0_11 = "(B01  B11  B41  B30) + (B01  B11  B21  B51  B40) + (B01  B21  B31  B41  B10) + (B01  B21  B41  B51  B30) + (B11  B21  B41  B51  B30) + (B31  B20  B40  B50) + (B41  B20  B30  B50) + (B11  B31  B51  B00  B20) + (B11  B31  B51  B00  B40) + (B31  B41  B51  B10  B20) + (B01  B11  B20  B40  B50) + (B21  B51  B00  B10  B40) + (B41  B51  B00  B10  B20) + (B11  B21  B31  B41  B00  B50) + (B31  B00  B10  B40  B50) + (B41  B00  B10  B30  B50) + (B00  B10  B20  B40  B50) + (B01  B21  B10  B30  B40  B50) + (B01  B51  B10  B20  B30  B40)"
Z0_20 = "(B31  B41  B51  B20) + (B11  B21  B00  B40) + (B01  B11  B21  B41  B50) + (B01  B11  B41  B51  B20) + (B11  B21  B31  B51  B00) + (B01  B11  B31  B20  B40) + (B01  B11  B31  B40  B50) + (B01  B21  B51  B30  B40) + (B01  B31  B41  B10  B50) + (B21  B31  B41  B10  B50) + (B21  B31  B51  B10  B40) + (B21  B41  B51  B10  B30) + (B11  B41  B00  B20  B50) + (B11  B51  B00  B30  B40) + (B01  B10  B20  B30  B50) + (B31  B00  B10  B40  B50) + (B41  B00  B20  B30  B50)"
Z0_21 = "(B01  B11  B21  B31  B51) + (B11  B21  B41  B51  B30) + (B21  B31  B41  B51  B10) + (B21  B10  B30  B50) + (B51  B10  B20  B30) + (B51  B10  B20  B40) + (B01  B11  B41  B20  B50) + (B11  B21  B41  B00  B50) + (B11  B41  B51  B00  B30) + (B00  B10  B30  B40) + (B01  B11  B20  B30  B40) + (B01  B11  B30  B40  B50) + (B01  B31  B10  B40  B50) + (B11  B31  B00  B20  B40) + (B11  B00  B20  B40  B50) + (B31  B41  B00  B10  B20  B50)"
Z0_30 = "(B00  B10  B20  B31  B50) + (B00  B20  B30  B40  B51) + (B00  B11  B20  B40  B51) + (B00  B11  B30  B40  B50) + (B00  B11  B21  B41  B51) + (B00  B10  B41  B50) + (B00  B10  B31  B41) + (B00  B21  B31  B41) + (B01  B10  B30  B40  B50) + (B01  B10  B30  B41  B51) + (B01  B10  B31  B40  B51) + (B01  B11  B20  B31  B50) + (B01  B11  B20  B41  B50) + (B01  B11  B20  B31  B41) + (B01  B11  B21  B40) + (B10  B21  B31  B41) + (B10  B21  B31  B51)"
Z0_31 = "(B01  B11  B21  B41) + (B11  B41  B00  B20) + (B01  B11  B51  B20  B30) + (B01  B11  B51  B20  B40) + (B01  B31  B41  B10  B20) + (B11  B21  B51  B00  B40) + (B01  B11  B20  B30  B40) + (B01  B31  B10  B40  B50) + (B01  B41  B10  B30  B50) + (B01  B51  B10  B30  B40) + (B11  B31  B00  B40  B50) + (B11  B41  B00  B30  B50) + (B21  B31  B10  B40  B50) + (B21  B51  B00  B30  B40) + (B41  B51  B00  B10  B30) + (B00  B10  B30  B40  B50) + (B31  B51  B00  B10  B20  B40)"
# Z0 = [Z0_00, Z0_01, Z0_10, Z0_11]
Z0 = [Z0_00, Z0_01, Z0_10, Z0_11, Z0_20, Z0_21, Z0_30, Z0_31]

# SBOX 1
Z1_31 = "(B01  B11  B21  B41  B51) + (B01  B21  B31  B41  B10) + (B11  B21  B31  B41  B00) + (B01  B11  B51  B20  B40) + (B01  B21  B31  B40  B50) + (B11  B21  B41  B30  B50) + (B01  B11  B20  B30  B40) + (B01  B31  B10  B40  B50) + (B01  B41  B10  B20  B30) + (B01  B51  B10  B30  B40) + (B11  B21  B00  B30  B40) + (B11  B51  B00  B20  B30) + (B31  B41  B00  B10  B20) + (B31  B51  B00  B10  B40) + (B01  B11  B31  B41  B20  B50) + (B21  B41  B51  B00  B10  B30) + (B00  B10  B20  B30  B50) + (B00  B10  B30  B40  B50) + (B11  B31  B00  B20  B40  B50)"
Z1_30 = "(B01  B11  B21  B51  B40) + (B01  B11  B41  B51  B20) + (B01  B11  B21  B30  B40) + (B01  B11  B41  B20  B30) + (B01  B21  B41  B10  B30) + (B01  B31  B41  B10  B20) + (B01  B31  B51  B10  B40) + (B11  B21  B31  B00  B40) + (B11  B31  B41  B00  B20) + (B11  B31  B51  B00  B40) + (B21  B31  B41  B00  B10) + (B01  B11  B21  B31  B41  B50) + (B21  B41  B10  B30  B50) + (B11  B21  B41  B51  B00  B30) + (B01  B10  B30  B40  B50) + (B11  B00  B20  B30  B50) + (B31  B00  B10  B40  B50) + (B51  B00  B10  B20  B30) + (B51  B00  B10  B30  B40) + (B01  B11  B31  B20  B40  B50)"
Z1_21 = "(B21  B41  B51  B30) + (B11  B21  B40  B50) + (B01  B11  B21  B31  B50) + (B01  B11  B31  B51  B20) + (B01  B11  B41  B51  B30) + (B01  B21  B31  B51  B10) + (B11  B21  B41  B51  B00) + (B31  B10  B20  B50) + (B01  B11  B30  B40  B50) + (B01  B21  B30  B40  B50) + (B01  B41  B10  B20  B50) + (B11  B41  B00  B30  B50) + (B11  B51  B00  B20  B40) + (B21  B51  B00  B10  B40) + (B31  B41  B00  B10  B50) + (B41  B51  B00  B10  B30) + (B00  B10  B20  B40  B50) + (B01  B51  B10  B20  B30  B40)"
Z1_20 = "(B11  B21  B51  B40) + (B01  B11  B21  B31  B51) + (B11  B31  B20  B50) + (B31  B51  B10  B20) + (B01  B11  B41  B30  B50) + (B01  B11  B51  B30  B40) + (B01  B21  B31  B10  B50) + (B01  B21  B41  B10  B50) + (B01  B21  B51  B30  B40) + (B01  B41  B51  B10  B20) + (B11  B31  B41  B00  B50) + (B11  B41  B51  B00  B20) + (B31  B41  B51  B00  B10) + (B11  B00  B20  B40  B50) + (B21  B00  B10  B40  B50) + (B41  B00  B10  B30  B50) + (B51  B00  B10  B20  B40) + (B01  B10  B20  B30  B40  B50)"
Z1_11 = "(B01  B11  B31  B40) + (B11  B21  B31  B41  B00) + (B11  B31  B41  B51  B00) + (B21  B31  B41  B51  B10) + (B31  B10  B20  B40) + (B31  B20  B40  B50) + (B01  B11  B21  B30  B50) + (B01  B21  B51  B10  B30) + (B01  B31  B41  B10  B50) + (B01  B41  B51  B20  B30) + (B11  B21  B51  B00  B30) + (B10  B20  B40  B50) + (B11  B21  B30  B40  B50) + (B11  B51  B00  B30  B40) + (B21  B51  B10  B30  B40) + (B31  B00  B10  B40  B50) + (B11  B41  B00  B20  B30  B50) + (B21  B41  B00  B10  B30  B50)"
Z1_10 = "(B01  B11  B31  B41) + (B01  B11  B21  B51  B30) + (B41  B00  B10  B20) + (B01  B21  B31  B10  B40) + (B11  B21  B31  B00  B40) + (B11  B31  B51  B00  B40) + (B21  B31  B51  B10  B40) + (B31  B41  B51  B10  B20) + (B01  B41  B10  B30  B50) + (B01  B41  B20  B30  B50) + (B01  B51  B20  B30  B40) + (B31  B41  B00  B10  B50) + (B31  B41  B00  B20  B50) + (B41  B51  B00  B10  B30) + (B41  B51  B00  B20  B30) + (B11  B20  B30  B40  B50) + (B21  B10  B30  B40  B50) + (B51  B10  B20  B30  B40) + (B11  B21  B41  B00  B30  B50)"
Z1_01 = "(B01  B11  B31  B41) + (B11  B31  B41  B51) + (B21  B51  B00  B40) + (B01  B10  B20  B40) + (B01  B11  B21  B30  B40) + (B01  B21  B41  B10  B50) + (B01  B31  B51  B20  B40) + (B01  B41  B51  B10  B30) + (B00  B20  B30  B50) + (B20  B30  B40  B50) + (B11  B41  B00  B30  B50) + (B21  B31  B00  B10  B50) + (B41  B51  B00  B10  B20) + (B11  B00  B20  B40  B50)"
Z1_00 = "(B01  B11  B41  B30) + (B01  B21  B31  B40) + (B01  B21  B10  B40) + (B11  B51  B20  B30) + (B01  B31  B41  B51  B10) + (B21  B31  B41  B51  B10) + (B51  B00  B20  B40) + (B01  B11  B31  B40  B50) + (B11  B31  B41  B00  B50) + (B21  B41  B51  B00  B30) + (B01  B41  B10  B20  B50) + (B11  B21  B00  B40  B50) + (B21  B00  B10  B30  B50) + (B31  B00  B10  B20  B50)"
Z1 = [Z1_00, Z1_01, Z1_10, Z1_11, Z1_20, Z1_21, Z1_30, Z1_31]
 
# SBOX 2
Z2_31 = "(B01  B11  B21  B31  B41  B51) + (B01  B11  B21  B30  B50) + (B01  B11  B21  B40  B50) + (B01  B11  B41  B20  B50) + (B01  B11  B51  B20  B30) + (B01  B11  B51  B20  B40) + (B01  B21  B51  B10  B30) + (B01  B21  B51  B10  B40) + (B01  B31  B41  B10  B20) + (B01  B31  B41  B10  B50) + (B11  B21  B51  B00  B30) + (B11  B31  B51  B00  B20) + (B11  B41  B20  B30  B50) + (B31  B41  B10  B20  B50) + (B11  B21  B31  B41  B00  B50) + (B21  B31  B41  B51  B00  B10) + (B21  B00  B10  B30  B50) + (B21  B00  B10  B40  B50) + (B21  B00  B30  B40  B50) + (B51  B00  B10  B20  B30) + (B51  B00  B10  B20  B40) + (B10  B20  B30  B40  B50)"
Z2_30 = "(B01  B11  B21  B51  B30) + (B01  B11  B21  B51  B40) + (B11  B21  B31  B51  B00) + (B11  B20  B40  B50) + (B31  B20  B40  B50) + (B01  B11  B21  B31  B41  B50) + (B01  B11  B31  B41  B51  B20) + (B01  B21  B31  B41  B51  B10) + (B01  B21  B10  B30  B50) + (B01  B21  B10  B40  B50) + (B01  B51  B10  B20  B30) + (B01  B51  B10  B20  B40) + (B11  B31  B00  B20  B50) + (B11  B31  B00  B40  B50) + (B11  B51  B00  B20  B30) + (B21  B51  B00  B10  B30) + (B21  B51  B00  B10  B40) + (B41  B10  B20  B30  B50) + (B11  B21  B41  B00  B30  B50) + (B21  B31  B41  B00  B10  B50) + (B31  B41  B51  B00  B10  B20)"
Z2_21 = "(B01  B11  B21  B31  B51) + (B21  B41  B30  B50) + (B01  B11  B41  B51  B20) + (B11  B21  B41  B51  B00) + (B01  B21  B51  B10  B30) + (B01  B31  B41  B10  B50) + (B01  B41  B51  B10  B30) + (B31  B41  B51  B00  B10) + (B01  B11  B20  B40  B50) + (B11  B21  B00  B40  B50) + (B11  B41  B00  B20  B50) + (B11  B51  B00  B20  B40) + (B21  B31  B10  B40  B50) + (B01  B20  B30  B40  B50) + (B31  B00  B10  B40  B50) + (B51  B00  B10  B30  B40) + (B01  B31  B51  B10  B20  B40)"
Z2_20 = "(B01  B11  B21  B31  B50) + (B01  B11  B21  B51  B30) + (B01  B31  B41  B51  B10) + (B01  B11  B41  B20  B50) + (B01  B11  B51  B20  B40) + (B11  B21  B51  B00  B40) + (B11  B41  B51  B00  B20) + (B21  B31  B41  B00  B50) + (B21  B31  B51  B10  B40) + (B01  B21  B30  B40  B50) + (B01  B51  B20  B30  B40) + (B31  B51  B00  B10  B40) + (B41  B51  B00  B10  B30) + (B11  B00  B20  B40  B50) + (B41  B00  B10  B20  B50) + (B41  B10  B20  B30  B50) + (B00  B10  B30  B40  B50) + (B01  B31  B10  B20  B40  B50)"
Z2_11 = "(B21  B41  B51  B10) + (B21  B31  B00  B10) + (B21  B31  B10  B50) + (B01  B11  B21  B31  B40) + (B01  B11  B21  B41  B30) + (B01  B11  B41  B51  B30) + (B11  B31  B41  B51  B00) + (B31  B00  B10  B50) + (B31  B10  B40  B50) + (B01  B31  B51  B10  B20) + (B01  B11  B20  B30  B40) + (B11  B21  B00  B30  B50) + (B11  B31  B00  B20  B40) + (B11  B51  B00  B20  B40) + (B41  B51  B00  B10  B30) + (B01  B11  B31  B41  B20  B50) + (B00  B10  B20  B40  B50) + (B01  B41  B10  B20  B30  B50)"
Z2_10 = "(B01  B11  B31  B41  B51) + (B01  B21  B30  B40) + (B11  B21  B31  B41  B50) + (B01  B10  B30  B40) + (B21  B10  B30  B50) + (B51  B10  B30  B40) + (B01  B11  B31  B20  B40) + (B01  B21  B51  B10  B40) + (B11  B21  B31  B00  B40) + (B11  B21  B51  B00  B40) + (B11  B31  B41  B00  B50) + (B11  B41  B51  B00  B30) + (B01  B51  B10  B20  B30) + (B11  B41  B20  B30  B50) + (B31  B51  B00  B10  B20) + (B11  B00  B20  B30  B50) + (B41  B00  B20  B30  B50) + (B01  B31  B41  B10  B20  B50)"
Z2_01 = "(B01  B11  B31  B41  B50) + (B01  B11  B31  B51  B40) + (B01  B11  B41  B51  B30) + (B01  B31  B41  B51  B20) + (B41  B00  B10  B20) + (B41  B00  B20  B30) + (B01  B21  B41  B10  B50) + (B11  B21  B31  B41  B51  B00) + (B01  B11  B30  B40  B50) + (B01  B51  B10  B30  B40) + (B11  B31  B00  B20  B40) + (B11  B31  B00  B40  B50) + (B11  B41  B00  B30  B50) + (B21  B31  B00  B10  B40) + (B01  B10  B20  B40  B50) + (B21  B00  B10  B40  B50) + (B51  B10  B20  B30  B40) + (B11  B21  B51  B00  B30  B40)"
Z2_00 = "(B01  B21  B31  B41  B51) + (B21  B41  B00  B10) + (B01  B11  B31  B40  B50) + (B01  B11  B41  B30  B50) + (B01  B11  B51  B30  B40) + (B01  B31  B51  B10  B40) + (B01  B41  B51  B10  B30) + (B11  B31  B41  B00  B20) + (B11  B31  B41  B00  B50) + (B21  B41  B51  B00  B30) + (B01  B21  B10  B40  B50) + (B01  B41  B10  B20  B50) + (B21  B51  B00  B10  B30) + (B11  B21  B31  B51  B00  B40) + (B11  B00  B20  B30  B40) + (B11  B00  B30  B40  B50) + (B31  B00  B10  B20  B40) + (B00  B10  B20  B40  B50)"
Z2 = [Z2_00, Z2_01, Z2_10, Z2_11, Z2_20, Z2_21, Z2_30, Z2_31]

# SBOX 3
Z3_31 = "(B01  B11  B21  B41) + (B11  B31  B41  B50) + (B01  B21  B31  B41  B50) + (B01  B21  B31  B51  B40) + (B11  B21  B41  B51  B30) + (B01  B11  B31  B20  B50) + (B01  B31  B51  B10  B20) + (B11  B31  B51  B00  B40) + (B01  B11  B20  B30  B40) + (B21  B31  B00  B40  B50) + (B31  B41  B00  B20  B50) + (B31  B51  B00  B20  B40) + (B41  B51  B10  B20  B30) + (B21  B31  B41  B51  B00  B10) + (B01  B10  B30  B40  B50) + (B11  B20  B30  B40  B50) + (B21  B00  B10  B30  B50) + (B51  B00  B10  B30  B40)"
Z3_30 = "(B11  B21  B30  B40) + (B11  B41  B20  B30) + (B01  B11  B31  B51  B20) + (B01  B21  B41  B51  B10) + (B11  B31  B41  B51  B00) + (B01  B21  B31  B40  B50) + (B21  B41  B51  B10  B30) + (B31  B41  B51  B00  B20) + (B01  B31  B10  B20  B50) + (B01  B41  B10  B30  B50) + (B01  B51  B10  B30  B40) + (B11  B21  B00  B30  B50) + (B11  B51  B00  B30  B40) + (B31  B00  B20  B40  B50) + (B21  B31  B41  B00  B10  B50) + (B21  B31  B51  B00  B10  B40) + (B00  B10  B20  B30  B50)"
Z3_21 = "(B11  B21  B41  B00) + (B01  B11  B31  B41  B51) + (B01  B31  B41  B51  B20) + (B01  B11  B21  B30  B50) + (B01  B11  B41  B20  B30) + (B01  B11  B51  B30  B40) + (B21  B31  B41  B10  B50) + (B21  B31  B51  B00  B40) + (B21  B31  B51  B10  B40) + (B01  B31  B20  B40  B50) + (B11  B31  B00  B20  B50) + (B31  B51  B00  B10  B40) + (B41  B51  B00  B10  B20) + (B01  B21  B41  B51  B10  B30) + (B01  B10  B20  B30  B50) + (B11  B00  B20  B30  B40) + (B00  B10  B30  B40  B50)"
Z3_20 = "(B21  B31  B40  B50) + (B01  B11  B21  B31  B40) + (B01  B11  B31  B41  B50) + (B21  B31  B41  B51  B10) + (B51  B10  B30  B40) + (B01  B31  B51  B20  B40) + (B11  B31  B51  B00  B20) + (B01  B11  B21  B41  B51  B30) + (B01  B21  B10  B30  B50) + (B01  B51  B10  B20  B30) + (B11  B21  B00  B30  B40) + (B11  B41  B00  B20  B30) + (B21  B41  B00  B10  B30) + (B31  B41  B10  B20  B50) + (B31  B00  B10  B20  B50) + (B41  B00  B20  B30  B50) + (B01  B11  B20  B30  B40  B50)"
Z3_11 = "(B01  B11  B21  B41  B51) + (B11  B31  B40  B50) + (B01  B11  B21  B51  B30) + (B01  B11  B31  B41  B20) + (B01  B21  B31  B41  B10) + (B51  B20  B30  B40) + (B11  B21  B31  B00  B50) + (B11  B31  B51  B00  B20) + (B21  B41  B51  B00  B30) + (B01  B21  B10  B30  B50) + (B01  B31  B10  B20  B40) + (B11  B41  B20  B30  B50) + (B41  B51  B00  B10  B30) + (B21  B00  B30  B40  B50) + (B21  B31  B51  B00  B10  B40) + (B00  B10  B20  B30  B40) + (B31  B41  B00  B10  B20  B50)"
Z3_10 = "(B01  B41  B10  B20) + (B01  B11  B21  B41  B50) + (B01  B11  B31  B51  B40) + (B11  B21  B31  B51  B00) + (B01  B21  B31  B10  B40) + (B01  B21  B51  B10  B30) + (B11  B41  B51  B20  B30) + (B21  B31  B41  B00  B10) + (B01  B11  B30  B40  B50) + (B21  B41  B00  B30  B50) + (B21  B51  B00  B30  B40) + (B31  B51  B00  B10  B20) + (B01  B20  B30  B40  B50) + (B11  B20  B30  B40  B50) + (B31  B00  B10  B40  B50) + (B41  B00  B10  B30  B50) + (B11  B31  B41  B00  B20  B50)"
Z3_01 = "(B41  B51  B10  B30) + (B01  B11  B31  B51  B20) + (B01  B21  B41  B51  B30) + (B11  B21  B31  B41  B50) + (B41  B00  B10  B20) + (B01  B11  B31  B40  B50) + (B11  B31  B51  B00  B40) + (B21  B31  B51  B10  B40) + (B01  B21  B30  B40  B50) + (B01  B51  B20  B30  B40) + (B11  B21  B00  B30  B50) + (B21  B31  B00  B10  B40) + (B21  B51  B00  B10  B30) + (B31  B41  B10  B20  B50) + (B41  B51  B00  B20  B30) + (B01  B11  B41  B20  B30  B50) + (B00  B20  B30  B40  B50) + (B10  B20  B30  B40  B50)"
Z3_00 = "(B21  B31  B41  B10) + (B01  B11  B21  B31  B51) + (B11  B31  B41  B51  B00) + (B31  B10  B20  B40) + (B01  B21  B41  B30  B50) + (B01  B21  B51  B30  B40) + (B01  B31  B51  B10  B20) + (B11  B21  B51  B00  B30) + (B11  B31  B41  B20  B50) + (B01  B31  B10  B40  B50) + (B01  B41  B10  B30  B50) + (B11  B31  B00  B40  B50) + (B11  B41  B00  B20  B50) + (B01  B11  B41  B51  B20  B30) + (B21  B00  B10  B30  B50) + (B51  B00  B20  B30  B40) + (B01  B11  B20  B30  B40  B50)"
Z3 = [Z3_00, Z3_01, Z3_10, Z3_11, Z3_20, Z3_21, Z3_30, Z3_31]

# SBOX 4
Z4_31 = "(B11  B31  B51  B40) + (B21  B31  B10  B50) + (B01  B11  B21  B41  B30) + (B11  B21  B31  B41  B00) + (B01  B20  B30  B40) + (B01  B11  B21  B30  B50) + (B01  B21  B41  B30  B50) + (B11  B21  B41  B30  B50) + (B11  B21  B51  B00  B40) + (B11  B41  B51  B20  B30) + (B01  B51  B10  B30  B40) + (B31  B51  B00  B20  B40) + (B41  B51  B00  B10  B30) + (B01  B11  B31  B41  B20  B50) + (B01  B31  B41  B51  B10  B20) + (B11  B00  B20  B40  B50) + (B41  B00  B10  B20  B50)"
Z4_30 = "(B21  B31  B51  B10) + (B01  B11  B31  B41  B51) + (B01  B11  B21  B31  B50) + (B01  B11  B31  B40  B50) + (B01  B41  B51  B10  B30) + (B31  B41  B51  B00  B20) + (B00  B10  B30  B40) + (B01  B31  B10  B20  B40) + (B01  B41  B10  B20  B50) + (B01  B41  B20  B30  B50) + (B11  B21  B00  B40  B50) + (B11  B41  B00  B20  B50) + (B01  B11  B21  B51  B30  B40) + (B11  B21  B41  B51  B00  B30) + (B21  B00  B10  B30  B50) + (B21  B10  B30  B40  B50) + (B51  B00  B20  B30  B40) + (B00  B10  B20  B40  B50)"
Z4_21 = "(B01  B11  B21  B51  B40) + (B01  B11  B41  B51  B20) + (B11  B21  B41  B51  B00) + (B01  B11  B21  B30  B40) + (B01  B21  B51  B30  B40) + (B01  B41  B51  B20  B30) + (B11  B31  B51  B20  B40) + (B01  B11  B21  B31  B41  B50) + (B01  B21  B31  B41  B51  B10) + (B01  B31  B10  B40  B50) + (B01  B31  B20  B40  B50) + (B01  B41  B10  B30  B50) + (B11  B41  B00  B30  B50) + (B31  B41  B00  B10  B20) + (B31  B41  B00  B10  B50) + (B41  B51  B00  B10  B30) + (B01  B10  B20  B40  B50) + (B11  B00  B20  B30  B50) + (B31  B10  B20  B40  B50) + (B51  B00  B10  B20  B30) + (B11  B21  B31  B00  B40  B50) + (B21  B31  B51  B00  B10  B40) + (B21  B00  B10  B30  B40  B50)"
Z4_20 = "(B01  B11  B21  B41  B51) + (B01  B21  B41  B51  B30) + (B01  B11  B41  B20  B50) + (B01  B11  B41  B30  B50) + (B01  B31  B41  B10  B20) + (B01  B31  B41  B10  B50) + (B01  B31  B51  B10  B40) + (B11  B21  B51  B00  B40) + (B11  B31  B41  B00  B50) + (B11  B41  B51  B00  B20) + (B01  B11  B20  B30  B50) + (B01  B51  B20  B30  B40) + (B11  B21  B00  B30  B40) + (B11  B31  B00  B20  B50) + (B11  B51  B20  B30  B40) + (B21  B51  B00  B30  B40) + (B31  B51  B10  B20  B40) + (B01  B11  B21  B31  B40  B50) + (B21  B31  B41  B51  B00  B10) + (B41  B00  B10  B30  B50) + (B00  B10  B20  B30  B50) + (B01  B21  B10  B30  B40  B50) + (B21  B31  B00  B10  B40  B50)"
Z4_11 = "(B01  B11  B21  B31  B41) + (B21  B41  B30  B50) + (B41  B51  B10  B20) + (B11  B31  B41  B51  B00) + (B31  B00  B10  B40) + (B31  B00  B40  B50) + (B01  B11  B31  B20  B40) + (B01  B31  B41  B10  B20) + (B01  B41  B51  B20  B30) + (B11  B21  B51  B30  B40) + (B21  B31  B51  B10  B40) + (B11  B51  B00  B30  B40) + (B21  B31  B00  B10  B50) + (B01  B10  B20  B30  B40) + (B01  B10  B30  B40  B50) + (B01  B20  B30  B40  B50) + (B10  B20  B30  B40  B50)"
Z4_10 = "(B21  B41  B51  B10) + (B21  B41  B51  B30) + (B21  B51  B10  B30) + (B01  B11  B21  B31  B40) + (B01  B11  B31  B41  B20) + (B41  B00  B20  B50) + (B41  B20  B30  B50) + (B01  B21  B31  B10  B50) + (B11  B31  B41  B00  B50) + (B11  B31  B51  B00  B40) + (B01  B31  B10  B20  B40) + (B11  B21  B30  B40  B50) + (B11  B41  B00  B20  B30) + (B11  B00  B30  B40  B50) + (B21  B00  B30  B40  B50) + (B51  B00  B10  B30  B40) + (B01  B11  B51  B20  B30  B40)"
Z4_01 = "(B01  B11  B21  B51) + (B11  B41  B51  B30) + (B01  B21  B31  B41  B51) + (B11  B21  B00  B30) + (B11  B41  B00  B30) + (B01  B21  B31  B40  B50) + (B01  B31  B41  B20  B50) + (B11  B21  B41  B00  B50) + (B11  B31  B51  B00  B20) + (B01  B11  B20  B40  B50) + (B01  B41  B10  B30  B50) + (B01  B51  B10  B20  B40) + (B21  B41  B10  B30  B50) + (B21  B51  B00  B10  B40) + (B41  B51  B00  B20  B30) + (B31  B00  B10  B20  B50) + (B31  B00  B10  B40  B50)"
Z4_00 = "(B01  B21  B31  B41  B50) + (B01  B31  B41  B51  B20) + (B21  B31  B41  B51  B00) + (B01  B11  B41  B30  B50) + (B01  B11  B51  B20  B40) + (B01  B21  B51  B10  B40) + (B01  B41  B51  B10  B30) + (B11  B21  B31  B00  B40) + (B21  B31  B41  B00  B10) + (B21  B41  B51  B10  B30) + (B00  B20  B30  B40) + (B10  B30  B40  B50) + (B01  B21  B30  B40  B50) + (B11  B31  B00  B20  B50) + (B31  B51  B00  B10  B20) + (B01  B10  B20  B40  B50) + (B00  B10  B20  B30  B50)"
Z4 = [Z4_00, Z4_01, Z4_10, Z4_11, Z4_20, Z4_21, Z4_30, Z4_31]

# SBOX 5
Z5_31 = "(B21  B31  B51  B10) + (B01  B11  B21  B31  B41) + (B01  B11  B21  B51  B40) + (B01  B11  B31  B20  B50) + (B01  B21  B31  B10  B40) + (B01  B21  B41  B30  B50) + (B01  B31  B51  B10  B40) + (B01  B41  B51  B20  B30) + (B11  B21  B31  B00  B50) + (B11  B31  B51  B00  B20) + (B00  B10  B30  B40) + (B11  B21  B00  B40  B50) + (B11  B21  B41  B51  B00  B30) + (B01  B20  B30  B40  B50) + (B31  B00  B10  B20  B50) + (B51  B00  B20  B30  B40) + (B11  B41  B00  B20  B30  B50)"
Z5_30 = "(B01  B21  B41  B51  B30) + (B01  B31  B41  B51  B20) + (B11  B21  B31  B51  B00) + (B41  B00  B10  B30) + (B01  B11  B21  B40  B50) + (B01  B11  B51  B20  B40) + (B01  B31  B41  B10  B50) + (B11  B21  B51  B00  B40) + (B01  B21  B10  B30  B40) + (B01  B31  B10  B20  B50) + (B01  B41  B20  B30  B50) + (B01  B51  B20  B30  B40) + (B11  B31  B00  B20  B50) + (B21  B31  B00  B10  B50) + (B21  B41  B00  B30  B50) + (B31  B51  B00  B10  B20) + (B41  B51  B00  B20  B30) + (B11  B00  B20  B40  B50)"
Z5_21 = "(B11  B21  B31  B41  B51) + (B01  B11  B41  B51  B30) + (B01  B11  B31  B20  B40) + (B01  B11  B31  B40  B50) + (B11  B21  B41  B30  B50) + (B11  B21  B51  B30  B40) + (B11  B31  B41  B00  B20) + (B21  B31  B51  B10  B40) + (B01  B11  B20  B40  B50) + (B01  B21  B10  B30  B50) + (B01  B31  B20  B40  B50) + (B01  B41  B10  B30  B50) + (B11  B21  B00  B30  B50) + (B11  B41  B00  B20  B50) + (B11  B51  B00  B30  B40) + (B21  B31  B00  B10  B50) + (B21  B51  B00  B30  B40) + (B31  B41  B00  B20  B50) + (B41  B51  B00  B10  B30) + (B01  B31  B41  B51  B10  B20) + (B01  B51  B10  B20  B30  B40) + (B00  B10  B20  B30  B40  B50)"
Z5_20 = "(B01  B31  B41  B50) + (B01  B11  B31  B41  B20) + (B11  B21  B31  B51  B40) + (B21  B31  B41  B51  B10) + (B31  B00  B20  B40) + (B01  B11  B41  B20  B50) + (B01  B21  B31  B10  B50) + (B01  B21  B51  B10  B30) + (B01  B41  B51  B10  B30) + (B11  B21  B31  B00  B50) + (B11  B41  B51  B00  B30) + (B31  B41  B51  B00  B10) + (B31  B51  B10  B20  B40) + (B11  B00  B20  B40  B50) + (B21  B00  B10  B30  B50) + (B41  B00  B10  B30  B50) + (B51  B00  B10  B20  B40) + (B01  B11  B21  B30  B40  B50) + (B01  B11  B51  B20  B30  B40) + (B01  B10  B20  B30  B40  B50)"
Z5_11 = "(B01  B11  B41  B51  B30) + (B11  B21  B31  B51  B40) + (B11  B21  B41  B51  B30) + (B21  B31  B41  B51  B00) + (B01  B11  B21  B30  B50) + (B01  B21  B51  B10  B40) + (B01  B41  B51  B10  B20) + (B11  B31  B41  B00  B50) + (B11  B31  B41  B20  B50) + (B01  B11  B30  B40  B50) + (B11  B21  B30  B40  B50) + (B11  B31  B00  B20  B50) + (B11  B51  B20  B30  B40) + (B21  B51  B10  B30  B40) + (B31  B41  B00  B20  B50) + (B41  B51  B10  B20  B30) + (B01  B21  B31  B41  B10  B50) + (B01  B10  B20  B30  B50) + (B01  B10  B20  B40  B50) + (B21  B00  B10  B30  B50) + (B21  B00  B10  B40  B50) + (B31  B51  B00  B10  B20  B40)"
Z5_10 = "(B11  B31  B51  B20) + (B01  B11  B21  B31  B41) + (B01  B21  B31  B41  B51) + (B01  B11  B31  B40  B50) + (B11  B21  B31  B40  B50) + (B11  B21  B51  B30  B40) + (B21  B41  B51  B10  B30) + (B31  B41  B51  B00  B20) + (B00  B20  B30  B50) + (B01  B21  B10  B30  B50) + (B01  B21  B10  B40  B50) + (B01  B51  B10  B20  B40) + (B11  B41  B00  B20  B30) + (B11  B41  B00  B30  B50) + (B11  B41  B20  B30  B50) + (B51  B10  B20  B30  B40) + (B01  B31  B41  B10  B20  B50) + (B21  B31  B41  B00  B10  B50) + (B21  B31  B51  B00  B10  B40) + (B00  B10  B20  B40  B50)"
Z5_01 = "(B01  B11  B21  B41  B51) + (B01  B31  B10  B40) + (B11  B41  B20  B50) + (B21  B41  B10  B50) + (B11  B20  B30  B50) + (B01  B11  B51  B20  B40) + (B01  B21  B31  B40  B50) + (B01  B41  B51  B10  B30) + (B11  B21  B51  B00  B40) + (B11  B31  B41  B00  B50) + (B31  B41  B51  B00  B10) + (B31  B41  B51  B00  B20) + (B11  B00  B30  B40  B50) + (B31  B10  B20  B40  B50) + (B51  B00  B10  B20  B30) + (B51  B00  B10  B30  B40)"
Z5_00 = "(B01  B21  B30  B40) + (B01  B11  B21  B41  B50) + (B01  B11  B21  B51  B40) + (B01  B11  B41  B51  B20) + (B01  B31  B41  B51  B10) + (B11  B21  B41  B51  B00) + (B01  B10  B30  B40) + (B41  B10  B20  B50) + (B11  B21  B41  B30  B50) + (B21  B41  B51  B00  B30) + (B10  B30  B40  B50) + (B11  B31  B20  B40  B50) + (B11  B51  B00  B20  B30) + (B11  B51  B00  B20  B40) + (B21  B31  B00  B40  B50) + (B31  B51  B00  B10  B40)"
Z5 = [Z5_00, Z5_01, Z5_10, Z5_11, Z5_20, Z5_21, Z5_30, Z5_31]

# SBOX 6
Z6_31 = "(B01  B11  B21  B41  B51) + (B11  B21  B00  B40) + (B21  B51  B30  B40) + (B01  B11  B21  B41  B30) + (B01  B11  B31  B40  B50) + (B01  B11  B51  B30  B40) + (B01  B21  B51  B10  B40) + (B01  B41  B51  B10  B20) + (B11  B31  B41  B20  B50) + (B11  B41  B51  B00  B30) + (B41  B51  B00  B20  B30) + (B01  B21  B31  B41  B10  B50) + (B21  B31  B41  B51  B00  B10) + (B01  B10  B20  B30  B50) + (B01  B10  B30  B40  B50) + (B11  B00  B20  B30  B50) + (B31  B00  B10  B20  B40) + (B31  B00  B10  B40  B50) + (B21  B41  B00  B10  B30  B50)"
Z6_30 = "(B11  B31  B51  B20) + (B01  B11  B31  B51  B40) + (B01  B21  B41  B51  B10) + (B11  B21  B31  B41  B50) + (B11  B31  B41  B51  B00) + (B01  B11  B41  B20  B30) + (B01  B21  B41  B10  B30) + (B11  B21  B41  B00  B50) + (B21  B41  B51  B10  B30) + (B01  B11  B30  B40  B50) + (B01  B31  B10  B40  B50) + (B01  B51  B10  B20  B40) + (B11  B31  B00  B20  B40) + (B31  B41  B00  B10  B20) + (B31  B41  B00  B10  B50) + (B31  B41  B10  B20  B50) + (B41  B00  B10  B20  B50) + (B51  B00  B20  B30  B40) + (B21  B31  B51  B00  B10  B40) + (B00  B10  B30  B40  B50)"
Z6_21 = "(B01  B11  B21  B41) + (B11  B21  B00  B40) + (B11  B21  B30  B50) + (B01  B11  B31  B41  B50) + (B01  B11  B31  B51  B40) + (B01  B11  B41  B51  B30) + (B11  B41  B51  B00  B20) + (B10  B20  B40  B50) + (B01  B41  B10  B30  B50) + (B01  B51  B10  B30  B40) + (B11  B41  B00  B30  B50) + (B11  B51  B00  B30  B40) + (B31  B41  B00  B10  B50) + (B31  B51  B00  B10  B40) + (B01  B31  B41  B51  B10  B20) + (B21  B41  B51  B00  B10  B30)"
Z6_20 = "(B01  B21  B41  B51  B10) + (B11  B21  B41  B51  B00) + (B11  B20  B40  B50) + (B21  B10  B40  B50) + (B01  B11  B31  B40  B50) + (B01  B11  B51  B30  B40) + (B01  B31  B41  B10  B50) + (B01  B31  B51  B10  B40) + (B11  B31  B41  B00  B50) + (B31  B41  B51  B00  B10) + (B01  B11  B31  B41  B51  B20) + (B01  B11  B20  B30  B50) + (B11  B31  B00  B20  B40) + (B41  B51  B10  B20  B30) + (B41  B00  B10  B30  B50) + (B51  B00  B10  B30  B40)"
Z6_11 = "(B01  B31  B41  B20) + (B21  B31  B51  B40) + (B01  B41  B20  B50) + (B01  B11  B21  B31  B50) + (B01  B21  B31  B51  B10) + (B11  B21  B31  B51  B00) + (B21  B30  B40  B50) + (B11  B31  B41  B20  B50) + (B11  B31  B51  B00  B40) + (B01  B11  B21  B41  B51  B30) + (B01  B51  B20  B30  B40) + (B11  B21  B00  B30  B50) + (B21  B51  B00  B10  B30) + (B41  B51  B00  B20  B30) + (B11  B00  B30  B40  B50) + (B41  B10  B20  B30  B50) + (B21  B31  B41  B00  B10  B50) + (B31  B00  B10  B20  B40  B50)"
Z6_10 = "(B01  B31  B20  B40) + (B01  B11  B21  B31  B41  B51) + (B01  B20  B40  B50) + (B01  B21  B31  B10  B50) + (B01  B21  B41  B30  B50) + (B01  B21  B51  B10  B30) + (B01  B21  B51  B30  B40) + (B01  B41  B51  B20  B30) + (B11  B21  B31  B00  B50) + (B11  B21  B51  B00  B30) + (B31  B41  B51  B00  B10) + (B31  B41  B51  B00  B20) + (B11  B31  B20  B40  B50) + (B21  B31  B10  B40  B50) + (B21  B41  B10  B30  B50) + (B31  B41  B00  B10  B20) + (B51  B00  B10  B20  B40) + (B51  B00  B20  B30  B40) + (B00  B10  B20  B30  B40) + (B11  B41  B00  B20  B30  B50)"
Z6_01 = "(B01  B11  B41  B51  B30) + (B21  B31  B41  B51  B10) + (B01  B11  B31  B20  B50) + (B01  B11  B41  B20  B50) + (B01  B11  B51  B20  B30) + (B01  B41  B51  B20  B30) + (B11  B21  B31  B00  B50) + (B11  B31  B51  B00  B20) + (B11  B41  B51  B20  B30) + (B01  B11  B21  B31  B51  B40) + (B01  B21  B10  B30  B40) + (B01  B21  B10  B40  B50) + (B01  B21  B30  B40  B50) + (B21  B41  B00  B30  B50) + (B21  B41  B10  B30  B50) + (B21  B51  B00  B10  B40) + (B21  B51  B00  B30  B40) + (B01  B10  B30  B40  B50) + (B31  B00  B10  B20  B50) + (B41  B00  B10  B30  B50) + (B51  B00  B10  B30  B40) + (B01  B31  B51  B10  B20  B40) + (B11  B00  B20  B30  B40  B50)"
Z6_00 = "(B01  B11  B21  B31  B41) + (B01  B11  B21  B31  B50) + (B01  B11  B21  B41  B50) + (B01  B11  B31  B51  B20) + (B11  B21  B31  B51  B00) + (B01  B31  B41  B10  B20) + (B21  B31  B41  B10  B50) + (B21  B41  B51  B00  B30) + (B21  B41  B51  B10  B30) + (B01  B31  B10  B20  B50) + (B01  B41  B10  B20  B50) + (B11  B31  B00  B20  B50) + (B11  B41  B00  B20  B50) + (B21  B31  B00  B10  B50) + (B31  B51  B00  B10  B20) + (B41  B51  B00  B10  B30) + (B01  B11  B21  B51  B30  B40) + (B01  B21  B31  B51  B10  B40) + (B21  B00  B30  B40  B50) + (B00  B10  B30  B40  B50) + (B01  B11  B20  B30  B40  B50) + (B01  B51  B10  B20  B30  B40) + (B11  B51  B00  B20  B30  B40)"
Z6 = [Z6_00, Z6_01, Z6_10, Z6_11, Z6_20, Z6_21, Z6_30, Z6_31]

# SBOX 7
Z7_31 = "(B11  B21  B31  B41  B51) + (B01  B11  B31  B51  B40) + (B01  B21  B51  B10  B30) + (B01  B21  B51  B10  B40) + (B01  B41  B51  B20  B30) + (B11  B21  B41  B30  B50) + (B21  B31  B41  B10  B50) + (B21  B41  B51  B00  B30) + (B01  B11  B30  B40  B50) + (B01  B21  B10  B30  B40) + (B11  B31  B00  B20  B40) + (B11  B51  B00  B20  B40) + (B21  B31  B00  B10  B40) + (B31  B51  B00  B10  B20) + (B01  B11  B31  B41  B20  B50) + (B41  B00  B20  B30  B50) + (B41  B10  B20  B30  B50) + (B00  B10  B30  B40  B50) + (B01  B31  B10  B20  B40  B50)"
Z7_30 = "(B11  B21  B31  B50) + (B11  B21  B00  B40) + (B01  B11  B21  B51  B30) + (B01  B31  B41  B51  B20) + (B21  B31  B41  B51  B10) + (B01  B11  B31  B40  B50) + (B01  B21  B31  B40  B50) + (B01  B31  B41  B10  B20) + (B01  B31  B51  B10  B20) + (B11  B31  B41  B00  B20) + (B01  B51  B20  B30  B40) + (B21  B41  B10  B30  B50) + (B41  B51  B00  B20  B30) + (B01  B10  B20  B30  B40) + (B11  B00  B30  B40  B50) + (B31  B00  B10  B20  B50) + (B51  B00  B10  B30  B40) + (B01  B11  B41  B20  B30  B50)"
Z7_21 = "(B01  B11  B41  B20) + (B01  B41  B20  B30) + (B31  B41  B00  B10) + (B01  B11  B21  B31  B40) + (B21  B31  B41  B51  B10) + (B01  B21  B31  B40  B50) + (B01  B21  B51  B30  B40) + (B11  B21  B41  B00  B50) + (B11  B41  B51  B00  B30) + (B01  B11  B20  B30  B50) + (B01  B21  B10  B30  B50) + (B11  B21  B00  B30  B50) + (B11  B31  B00  B20  B40) + (B21  B51  B00  B10  B40) + (B01  B31  B51  B10  B20  B40) + (B00  B10  B20  B30  B40) + (B00  B10  B20  B40  B50)"
Z7_20 = "(B11  B21  B31  B41  B51) + (B01  B21  B31  B41  B50) + (B01  B21  B41  B51  B30) + (B41  B00  B10  B30) + (B01  B11  B21  B30  B50) + (B01  B11  B31  B20  B40) + (B01  B31  B41  B10  B20) + (B11  B21  B31  B00  B40) + (B11  B31  B41  B00  B20) + (B01  B51  B20  B30  B40) + (B11  B51  B00  B30  B40) + (B01  B21  B31  B51  B10  B40) + (B01  B10  B20  B40  B50) + (B11  B00  B20  B30  B50) + (B21  B00  B10  B40  B50) + (B31  B51  B00  B10  B20  B40)"
Z7_11 = "(B11  B21  B41  B50) + (B01  B21  B31  B41  B51) + (B21  B41  B30  B50) + (B11  B20  B40  B50) + (B31  B10  B40  B50) + (B01  B11  B31  B20  B40) + (B01  B11  B31  B20  B50) + (B01  B21  B51  B30  B40) + (B01  B41  B51  B10  B20) + (B21  B31  B51  B00  B40) + (B31  B41  B51  B00  B20) + (B11  B51  B00  B20  B30) + (B21  B41  B00  B10  B30) + (B41  B00  B10  B30  B50) + (B51  B10  B20  B30  B40)"
Z7_10 = "(B11  B21  B40  B50) + (B31  B41  B10  B50) + (B01  B11  B41  B51  B20) + (B01  B21  B31  B51  B40) + (B01  B21  B41  B51  B30) + (B11  B21  B41  B51  B00) + (B21  B31  B41  B51  B00) + (B21  B00  B30  B40) + (B01  B11  B51  B20  B30) + (B01  B31  B51  B10  B40) + (B10  B30  B40  B50) + (B01  B41  B20  B30  B50) + (B11  B41  B00  B20  B50) + (B31  B51  B00  B20  B40) + (B41  B51  B00  B10  B20  B30)"
Z7_01 = "(B31  B41  B51  B20) + (B01  B11  B21  B31  B51) + (B11  B51  B30  B40) + (B01  B11  B41  B30  B50) + (B01  B21  B31  B10  B50) + (B01  B41  B51  B10  B30) + (B11  B21  B31  B00  B50) + (B11  B21  B51  B00  B30) + (B31  B41  B51  B00  B10) + (B01  B11  B20  B30  B40) + (B11  B31  B20  B40  B50) + (B11  B41  B20  B30  B50) + (B21  B31  B10  B40  B50) + (B31  B41  B00  B10  B20) + (B01  B10  B30  B40  B50) + (B51  B00  B10  B20  B40) + (B10  B20  B30  B40  B50) + (B21  B41  B00  B10  B30  B50)"
Z7_00 = "(B01  B51  B10  B40) + (B21  B51  B10  B40) + (B01  B11  B21  B31  B50) + (B01  B11  B41  B51  B30) + (B01  B21  B31  B51  B10) + (B11  B21  B31  B51  B00) + (B01  B11  B21  B40  B50) + (B11  B31  B41  B20  B50) + (B11  B31  B51  B20  B40) + (B01  B31  B10  B20  B50) + (B01  B41  B10  B30  B50) + (B11  B21  B00  B30  B50) + (B21  B51  B00  B10  B30) + (B41  B51  B00  B20  B30) + (B11  B00  B30  B40  B50) + (B21  B00  B10  B30  B40) + (B31  B10  B20  B40  B50) + (B41  B00  B10  B20  B30) + (B21  B31  B41  B00  B10  B50)"
Z7 = [Z7_00, Z7_01, Z7_10, Z7_11, Z7_20, Z7_21, Z7_30, Z7_31]

Z_test = "(B00  B11  B20  B40  B51) + (B00  B11  B30  B40  B50) + (B00  B10  B20  B31  B50) + (B00  B10  B41  B50) + (B00  B11  B21  B41  B51)  + (B10  B21  B31  B51)"
match_threshold = 2

# SBOXES = [Z0]
SBOXES = [Z0, Z1, Z2, Z3, Z4, Z5, Z6, Z7]

mc = MatchController(0)
mc.show_documentation()

for i in range(len(SBOXES)):
    MEMO = []
    for j in range(len(SBOXES[i])):
        RAIL = "RAIL0" if j % 2 == 0 else "RAIL1"
        z_idx = j // 2
        print(f"-- j = {j} --")
        print(f"-- SBOX : {i} Index : {z_idx} {RAIL} --")
        z = SBOXES[i][j]
        mc = MatchController(i)
        mc.set_RAIL(RAIL)
        mc.set_Z_INDEX(z_idx)
        mc.generate_case_list(z)
        mc.generate_pairs()
        mc.find_matches()
        mc.drop_bad_matches(match_threshold)
        mc.filter_remainders()
        mc.set_gates(gates)
        mc.set_input_groups()
        mc.set_input_groups_subset()
        mc.create_networkx_graph()
        mc.create_bipartite_graph()
        mc.show_statistics()
        mc.create_graph_matching()
        mc.create_matching_pairs()
        mc.create_z_outputs()
        mc.show_matched_gates()
        mc.show_remainders_gates()
        mc.show_or_tree_gate()

mc.show_signals()

# mc = MatchController()
# mc.generate_case_list(Z2_30)
# mc.generate_pairs()
# mc.find_matches()
# mc.drop_bad_matches(match_threshold)
# mc.filter_remainders()
# mc.set_gates(gates)
# mc.set_input_groups()
# mc.set_input_groups_subset()
# mc.create_networkx_graph()
# mc.create_bipartite_graph()
# mc.create_graph_matching()
# mc.create_matching_pairs()
# mc.show_matched_gates()
