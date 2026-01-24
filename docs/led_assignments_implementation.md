# LED Assignments Implementation

## Overview
This document describes the LED assignment system that allows mapping LEDs to pins and managing multiple sets of assignments.

## Key Features

### 1. Pin Mapping
- Each LED assignment includes a `pin` property that maps the LED to a specific pin
- Pin mapping is stored directly in the LED assignment data
- The mapping is independent of the environment configuration

### 2. Multiple Assignment Sets
- Support for multiple sets of LED assignments
- Each set can be loaded independently via the web interface
- Sets are stored in `config.yaml` under the `led_assignments` section

### 3. Web Interface
- **LED Assignment Page**: `/led-assignment`
- **Features**:
  - Visual map of the DESY plan with LED positions
  - Add new LEDs by clicking on the map
  - Assign pins to LEDs
  - Select and manage existing assignments
  - Switch between different assignment sets
  - Trigger LEDs in trigger mode
  - Visual indicators for pin assignments

### 4. API Endpoints

#### Get Assignments
- `GET /api/led-assignments?set=<set_name>` - Load assignments for a specific set
- `GET /api/led-assignments` - Load all assignments

#### Manage Sets
- `GET /api/led-assignment-sets` - List all assignment sets
- `POST /api/led-assignment-sets` - Create a new set
- `DELETE /api/led-assignment-sets/<set_name>` - Delete a set

#### Save Assignments
- `POST /api/led-assignments` - Save current assignments to config

#### Trigger LEDs
- `POST /api/trigger` - Trigger a specific LED by pin number

## Configuration Structure

### config.yaml
```yaml
led_assignments:
  default:
    name: Default Assignment
    description: Default LED assignment set
    assignments: null
  
  set_name_1:
    name: Set Name 1
    description: Description
    assignments:
      LED_1234567890:
        x: 100
        y: 200
        pin: 5
  
  set_name_2:
    name: Set Name 2
    description: Another set
    assignments:
      LED_9876543210:
        x: 300
        y: 400
        pin: 10
```

## Usage

### Adding a New LED
1. Navigate to `/led-assignment`
2. Switch to "Assign" mode
3. Click on the map to add a new LED
4. Enter the pin number in the popup panel
5. Click "Save" to persist the assignment

### Switching Assignment Sets
1. Use the dropdown menu to select a different set
2. The map and assignments will update automatically

### Triggering an LED
1. Navigate to `/led-assignment`
2. Switch to "Trigger" mode
3. Click on an LED on the map
4. The LED will be triggered via its assigned pin

## Implementation Details

### Frontend (JavaScript)
- **led_assignment.js**: Main application logic
  - Handles map interactions
  - Manages assignment state
  - Communicates with API endpoints
  - Implements trigger mode
  - Manages multiple sets

- **led_assignment.html**: UI template
  - Map visualization
  - Control panels
  - Set management UI

### Backend (Python/Flask)
- **web_server.py**: API endpoints
  - Handles assignment CRUD operations
  - Manages set creation/deletion
  - Processes trigger requests

### Data Storage
- Assignments are persisted in `config.yaml`
- YAML format ensures human-readable configuration
- Automatic saving on changes

## Testing

Run the test suite:
```bash
python tests/test_led_assignments.py
```

## Future Enhancements

- [ ] Bulk import/export of assignments
- [ ] Visual editor for pin assignments
- [ ] Assignment validation
- [ ] Pin conflict detection
- [ ] Assignment templates
- [ ] Export assignments to JSON