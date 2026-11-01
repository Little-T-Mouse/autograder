"""Independently developed behavior checks for A1 scheduling."""
import pytest


def configuration(priority='volume', parcel_order='non-decreasing',
                  truck_order='non-decreasing'):
    return {
        'parcel_priority': priority,
        'parcel_order': parcel_order,
        'truck_order': truck_order,
    }


@pytest.mark.parametrize('priority,order,ids', [
    ('volume', 'non-decreasing', [9, 2, 5, 4]),
    ('volume', 'non-increasing', [4, 5, 9, 2]),
    ('destination', 'non-decreasing', [2, 4, 9, 5]),
    ('destination', 'non-increasing', [5, 9, 4, 2]),
])
def test_greedy_parcel_priority_and_stable_ties(priority, order, ids):
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler
    packages = [
        Parcel(9, 2, 'Base', 'Maple'),
        Parcel(2, 2, 'Base', 'Aspen'),
        Parcel(5, 3, 'Base', 'Zebra'),
        Parcel(4, 4, 'Base', 'Birch'),
    ]
    vehicle = Truck(1, 50, 'Base')
    original = packages[:]
    assert GreedyScheduler(configuration(priority, order)).schedule(packages, [vehicle]) == []
    assert [p.id_ for p in vehicle.parcel] == ids
    assert packages == original


@pytest.mark.parametrize('truck_order,truck_id', [
    ('non-decreasing', 2),
    ('non-increasing', 1),
])
def test_greedy_truck_order_uses_remaining_capacity(truck_order, truck_id):
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler
    trucks = [Truck(1, 25, 'Base'), Truck(2, 9, 'Base')]
    GreedyScheduler(configuration(truck_order=truck_order)).schedule(
        [Parcel(101, 3, 'Base', 'Harbor')], trucks
    )
    assert [t.id_ for t in trucks if t.parcel] == [truck_id]


def test_greedy_prefers_last_matching_city_even_if_other_truck_has_more_space():
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler
    small = Truck(1, 9, 'Base')
    large = Truck(2, 100, 'Base')
    small.pack(Parcel(1, 2, 'Base', 'Harbor'))
    shipment = Parcel(2, 3, 'Base', 'Harbor')
    GreedyScheduler(configuration(truck_order='non-increasing')).schedule(
        [shipment], [small, large]
    )
    assert small.parcel[-1] is shipment
    assert large.parcel == []


def test_greedy_keeps_tie_breaking_in_input_truck_order():
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler
    vehicles = [Truck(50, 15, 'Base'), Truck(2, 15, 'Base')]
    GreedyScheduler(configuration()).schedule(
        [Parcel(1, 4, 'Base', 'Elm')], vehicles
    )
    assert len(vehicles[0].parcel) == 1
    assert vehicles[1].parcel == []


def test_greedy_reports_parcels_that_cannot_fit():
    from domain import Parcel, Truck
    from scheduler import GreedyScheduler
    too_large = Parcel(5, 100, 'Base', 'Elm')
    fitting = Parcel(6, 3, 'Base', 'Birch')
    vehicle = Truck(1, 7, 'Base')
    remaining = GreedyScheduler(configuration()).schedule([too_large, fitting], [vehicle])
    assert remaining == [too_large]
    assert vehicle.parcel == [fitting]


def test_random_scheduler_keeps_inputs_intact_and_assigns_fitting_parcels():
    from domain import Parcel, Truck
    from scheduler import RandomScheduler
    packages = [Parcel(7, 4, 'Base', 'Elm'), Parcel(8, 4, 'Base', 'Birch')]
    original = packages[:]
    vehicles = [Truck(1, 4, 'Base'), Truck(2, 4, 'Base')]
    original_vehicles = vehicles[:]
    assert RandomScheduler().schedule(packages, vehicles) == []
    assert packages == original
    assert vehicles == original_vehicles
    assert sorted(p.id_ for t in vehicles for p in t.parcel) == [7, 8]
    assert all(t.used_space == 4 for t in vehicles)


def test_random_scheduler_handles_no_eligible_truck():
    from domain import Parcel, Truck
    from scheduler import RandomScheduler
    large_package = Parcel(77, 21, 'Base', 'Oak')
    untouched = Truck(1, 5, 'Base')
    assert RandomScheduler().schedule([large_package], [untouched]) == [large_package]
    assert untouched.parcel == []
