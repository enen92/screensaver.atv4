import json

# This utility is intended to ease the effort of manually merging new and old JSON entries.json


# Open the JSON files
# https://www.geeksforgeeks.org/read-json-file-using-python/#
oldEntriesFile = open('resources/entries.json')
newEntriesFile = open('resources/entriesnew4k.json')

# Convert the files into dicts
oldEntries = json.load(oldEntriesFile)
newEntries = json.load(newEntriesFile)

# Close the input files now that they're not in use
oldEntriesFile.close()
newEntriesFile.close()

# Create Sets that the shotIDs will be stored in
oldShotIDs = set()
newShotIDs = set()

# Iterate through the old entries file, adding the shotID to a set
for i in oldEntries['assets']:
    if 'shotID' in i:
        oldShotIDs.add(i['shotID'])
print('added all old shotIDs to a set')

# Iterate through the new entries file, adding the shotID to a set
for i in newEntries['assets']:
    # Safely handle shotID being missing from the dicct
    # https://www.scaler.com/topics/check-if-key-exists-in-dictionary-python/
    if 'shotID' in i:
        newShotIDs.add(i['shotID'])
print('added all new shotIDs to a set')

# Show the shotIDs in the new Entries but not in the old Entries
# https://www.geeksforgeeks.org/python-set-difference/
shotIDsToAdd = newShotIDs - oldShotIDs

# Create a List of all the assets to be output
updatedAssets = []

# Decorate all the existing assets with any new data that can be found in the new assets
for oldAsset in oldEntries['assets']:
    # Proceed only if there's a shotID to reference, otherwise just skip to adding it
    if 'shotID' in oldAsset:
        # Get the corresponding new asset from newEntries
        # https://stackoverflow.com/questions/8653516/search-a-list-of-dictionaries-in-python
        newAsset = next(item for item in newEntries['assets'] if item['shotID'] == oldAsset['shotID'])
        # For each of the newly introduced metadata key values
        for key in ['localizedNameKey', 'showInTopLevel', 'preferredOrder', 'previewImage', 'id', 'includeInShuffle',
                    'subcategories', 'url-4K-SDR-240FPS']:
            # Check that the new entry/asset actually has that key
            if key in newAsset:
                # Then put that new key value in the old asset
                oldAsset[key] = newAsset[key]

    # Finally add the newly decorated (or untouched) asset to the updatedAssets list
    updatedAssets.append(oldAsset)

for i in newEntries['assets']:
    # Handle the case where the shotID is entirely new, and needs to be added to the final set
    if i['shotID'] in shotIDsToAdd:
        # Decorate the new asset to indicate it was manually added
        i['official'] = 'kubedzero_manually_added'
        updatedAssets.append(i)

oldEntries['assets'] = updatedAssets
# Write the newly crafted JSON to disk
# NOTE that it can still be formatted with something such as jq or prettier
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(oldEntries, f, ensure_ascii=False, indent=4)
