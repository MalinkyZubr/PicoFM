def find_index(layer, adjacency):
    if adjacency % 2 == 0:
        index = 0
    else:
        index = 1
    layer -= 1
    adjacency //= 2

    while layer > 0:
        if adjacency % 2 == 0:
            index *= 2
        else:
            index = (index * 2) + 1
        
        layer -= 1
        adjacency //= 2

    return index

if __name__ == "__main__":
    print(find_index(3, 6))
    
