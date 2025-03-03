import pandas as pd
import networkx as nx

def load_data(adjacency_file, demographics_file, heirarchy_file):
    # Load adjacency as a graph
    adj_df = pd.read_csv(adjacency_file)
    G = nx.Graph()
    for _, row in adj_df.iterrows():
        G.add_edge(int(row['blockA']), int(row['blockB']))  # Convert to integers

    #Load heirarchy as a graph
    heir_df = pd.read_csv(heirarchy_file)
    H = nx.from_pandas_edgelist(heir_df, source='blockA', target='blockB', create_using=nx.DiGraph())
        
    # Load demographic data
    demo_df = pd.read_csv(demographics_file)
    demographics = {
        int(row['block']): {
            'population': float(row['population']), 
            'democrats': float(row['num_positive'])
        }
        for _, row in demo_df.iterrows()
    }
    
    return G, demographics

def initialize_districts(num_districts, target_population):
    districts = {i: {'blocks': set(), 'population': 0, 'democrats': 0} for i in range(num_districts)}
    return districts

def assign_block_to_district(district, block, demographics):
    district['blocks'].add(block)
    district['population'] += demographics[block]['population']
    district['democrats'] += demographics[block]['democrats']

def gerrymander(adjacency_file, demographics_file, num_districts, party):
    # Step 1: Load data
    G, demographics = load_data(adjacency_file, demographics_file)

    # Step 2: Calculate target population per district
    total_population = sum(d['population'] for d in demographics.values())
    target_population = total_population / num_districts

    print(target_population)

    # Step 3: Initialize districts
    districts = initialize_districts(num_districts, target_population)

    # Step 4: Sort blocks by favorability to the target party
    sorted_blocks = sorted(demographics.keys(), key=lambda b: favorability_score(demographics[b], party), reverse=True)

    # Step 5: Assign blocks to districts based on packing/cracking strategy
    for block in sorted_blocks:
        assigned = False
        for district in districts.values():
            # Ensure the block does not exceed target population
            if district['population'] + demographics[block]['population'] <= target_population:
                if is_contiguous(district, block, G) or district['population'] == 0:
                    assign_block_to_district(district, block, demographics)
                    assigned = True
                    break
        if not assigned:
            print(f"Block {block} could not be assigned due to population/contiguity constraints.")

    # Step 6: Refinement to balance populations across districts
    # refine_districts(districts, G, target_population, demographics)

    return [district['blocks'] for district in districts.values()]

def favorability_score(block_demo, party):
    # Calculate favorability score for a block for the given party
    if party == 'D':
        return block_demo['democrats'] / block_demo['population']
    else:
        if block_demo['population'] == 0:
            return 0
        return (block_demo['population'] - block_demo['democrats']) / block_demo['population']

def is_contiguous(district, block, G):
    # Check if the block is directly adjacent to any block in the district
    for b in district['blocks']:
        if G.has_edge(b, block):
            return True
    return False

def refine_districts(districts, G, target_population, demographics):
    for district in districts.values():
        while district['population'] > target_population:
            # Find a block to move out
            for block in list(district['blocks']):
                # Temporarily remove the block
                district['blocks'].remove(block)
                district['population'] -= demographics[block]['population']
                district['democrats'] -= demographics[block]['democrats']

                if not is_contiguous(district, block, G):
                    # Revert if contiguity is broken
                    district['blocks'].add(block)
                    district['population'] += demographics[block]['population']
                    district['democrats'] += demographics[block]['democrats']
                    continue

                # Move block to underpopulated district
                for other_district in districts.values():
                    if other_district['population'] + demographics[block]['population'] <= target_population:
                        assign_block_to_district(other_district, block, demographics)
                        break
                break
    
    print(f"Refining Districts...")
    for district_id, district in enumerate(districts.values()):
        print(f"Before Refinement - District {district_id}: Population: {district['population']}, Blocks: {district['blocks']}")
    refine_districts(districts, G, target_population, demographics)
    for district_id, district in enumerate(districts.values()):
        print(f"After Refinement - District {district_id}: Population: {district['population']}, Blocks: {district['blocks']}")


def gerrymander_debug(adjacency_file, demographics_file, num_districts, party):
    # Step 1: Load data
    G, demographics = load_data(adjacency_file, demographics_file)
    print("\nLoaded Data:")
    print(f"Total Blocks: {len(G.nodes)}")
    print(f"Total Edges: {len(G.edges)}")
    print(f"Demographics: {demographics}\n")
    
    # Step 2: Calculate target population per district
    total_population = sum(d['population'] for d in demographics.values())
    target_population = total_population // num_districts
    print(f"Total Population: {total_population}, Target Population per District: {target_population}\n")

    # Step 3: Initialize districts
    districts = initialize_districts(num_districts, target_population)

    # Step 4: Sort blocks by favorability to the target party
    sorted_blocks = sorted(demographics.keys(), key=lambda b: favorability_score(demographics[b], party), reverse=True)
    print(f"Sorted Blocks by Favorability: {sorted_blocks}\n")

    # Step 5: Assign blocks to districts with debug output
    for block in sorted_blocks:
        assigned = False
        print(f"Attempting to assign block {block} (population={demographics[block]['population']}, "
              f"democrats={demographics[block]['democrats']})")
        for district_id, district in districts.items():
            if district['population'] < target_population:
                # Temporarily bypass contiguity for debugging
                assign_block_to_district(district, block, demographics)
                assigned = True
                print(f"  -> Assigned block {block} to district {district_id}. "
                      f"District Population: {district['population']}")
                break
        if not assigned:
            print(f"  !! Block {block} could not be assigned under current constraints.\n")

    # Step 6: Print final district assignments
    print("\nFinal District Assignments:")
    for district_id, district in districts.items():
        print(f"District {district_id}: Blocks: {district['blocks']}, Population: {district['population']}, "
              f"Democrats: {district['democrats']}")

    return [district['blocks'] for district in districts.values()]

def main():
    # Input file paths
    adjacency_file = "blurred_adjacency.csv"
    demographics_file = "blurred_demographic.csv"

    # Number of districts and party to favor
    num_districts = 4
    party = 'R'  # 'R' for Republicans, 'D' for Democrats

    # Run the debugging version of the gerrymander algorithm
    results = gerrymander(adjacency_file, demographics_file, num_districts, party)


    # Load demographics to calculate statistics
    _, demographics = load_data(adjacency_file, demographics_file)

    # Print results for each district
    print("\nGerrymandering Results:")
    for district_id, blocks in enumerate(results):
        total_population = sum(demographics[block]['population'] for block in blocks)
        total_democrats = sum(demographics[block]['democrats'] for block in blocks)
        total_republicans = total_population - total_democrats

        print(f"\nDistrict {district_id}:")
        print(f"  Total Population: {total_population}")
        print(f"  Democrats: {total_democrats}")
        print(f"  Republicans: {total_republicans}")
        print(f"  Blocks: {sorted(blocks)}")

if __name__ == "__main__":
    main()
