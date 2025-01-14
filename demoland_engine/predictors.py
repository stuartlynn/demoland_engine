import pickle
import joblib
import pandas as pd

from .sampling import get_data
from .data import CACHE

with open(CACHE.fetch("air_quality_predictor"), "rb") as f:
    air_quality_predictor = pickle.load(f)

with open(CACHE.fetch("house_price_predictor"), "rb") as f:
    house_price_predictor = pickle.load(f)

with open(CACHE.fetch("accessibility"), "rb") as f:
    accessibility = joblib.load(f)


def get_indicators(df, mode="walk", random_seed=None):
    """Get indicators for all OAs based on 4 variables

    Parameters
    ----------
    df : DataFrame
        DataFrame reflecting the intended change of each OA.

        See the usage.ipynb for an example.

        The bounds of allowed values per column:

            signature_type : int
                Int representing signature type. See below the possible options
                and their relationship to the signature type.

                    0: 'Wild countryside',
                    1: 'Countryside agriculture',
                    2: 'Urban buffer',
                    3: 'Warehouse/Park land',
                    4: 'Open sprawl',
                    5: 'Disconnected suburbia',
                    6: 'Accessible suburbia',
                    7: 'Connected residential neighbourhoods',
                    8: 'Dense residential neighbourhoods',
                    9: 'Gridded residential quarters',
                    10: 'Dense urban neighbourhoods',
                    11: 'Local urbanity',
                    12: 'Regional urbanity',
                    13: 'Metropolitan urbanity',
                    14: 'Concentrated urbanity',
                    15: 'Hyper concentrated urbanity',

            use : float, optional
                Float in a range -1...1 reflecting the land use balance between
                fully residential (-1) and fully commercial (1). Defautls to 0,
                a value derived from signatures. For values < 0, we are allocating
                workplace population to residential population. For values > 0, we
                are allocating residential population to workplace population.
                Extremes are allowed but are not realistic, in most cases.
            greenspace : float, optional
                Float in a range 0...1 reflecting the amount of greenspace in the
                area. 0 representes no accessible greenspace, 1 represents whole
                area covered by a greenspace. This value will proportionally affect
                the amounts of jobs and population.
            job_types : float, optional
                Float in a range 0...1 reflecting the balance of job types in the
                area between entirely blue collar jobs (0) and entirely white collar
                jobs (1).
    mode : str, default "walk"
        Accessibility mode. One of {"transit", "car", "bike", "walk"}


    Returns
    -------
    DataFrame
        DataFrame containing the resulting indicators
    """
    vars, jobs, gsp = get_data(df, random_seed=random_seed)
    aq = air_quality_predictor.predict(vars)
    hp = house_price_predictor.predict(vars)
    ja = accessibility.job_accessibility(jobs, mode)
    gs = accessibility.greenspace_accessibility(gsp, mode)
    ja = ja.to_pandas()[df.index].values
    gs = gs.to_pandas()[df.index].values

    return pd.DataFrame(
        {
            "air_quality": aq,
            "house_price": hp,
            "job_accessibility": ja,
            "greenspace_accessibility": gs,
        },
        index=df.index,
    )


def get_indicators_lsoa(df):
    """Get indicators for all LSOAs based on 4 variables

    Parameters
    ----------
    df : DataFrame
        DataFrame reflecting the intended change of each OA.

        See the usage.ipynb for an example.

        The bounds of allowed values per column:

            signature_type : int
                Int representing signature type. See below the possible options
                and their relationship to the signature type.

                    0: 'Wild countryside',
                    1: 'Countryside agriculture',
                    2: 'Urban buffer',
                    3: 'Warehouse/Park land',
                    4: 'Open sprawl',
                    5: 'Disconnected suburbia',
                    6: 'Accessible suburbia',
                    7: 'Connected residential neighbourhoods',
                    8: 'Dense residential neighbourhoods',
                    9: 'Gridded residential quarters',
                    10: 'Dense urban neighbourhoods',
                    11: 'Local urbanity',
                    12: 'Regional urbanity',
                    13: 'Metropolitan urbanity',
                    14: 'Concentrated urbanity',
                    15: 'Hyper concentrated urbanity',

            use : float, optional
                Float in a range -1...1 reflecting the land use balance between
                fully residential (-1) and fully commercial (1). Defautls to 0,
                a value derived from signatures. For values < 0, we are allocating
                workplace population to residential population. For values > 0, we
                are allocating residential population to workplace population.
                Extremes are allowed but are not realistic, in most cases.
            greenspace : float, optional
                Float in a range 0...1 reflecting the amount of greenspace in the
                area. 0 representes no accessible greenspace, 1 represents whole
                area covered by a greenspace. This value will proportionally affect
                the amounts of jobs and population.
            job_types : float, optional
                Float in a range 0...1 reflecting the balance of job types in the
                area between entirely blue collar jobs (0) and entirely white collar
                jobs (1).


    Returns
    -------
    DataFrame
        DataFrame containing the resulting indicators
    """
    empty = pd.read_parquet(CACHE.fetch("empty.parquet"))
    lsoa_oa = pd.read_parquet(CACHE.fetch("oa_lsoa.parquet"))

    merged = (
        empty.assign(lsoa=lsoa_oa.lsoa11cd)[["lsoa"]]
        .merge(df, left_on="lsoa", right_index=True, how="left")
        .drop(columns="lsoa")
    )
    return get_indicators(merged).assign(lsoa=lsoa_oa.lsoa11cd).groupby("lsoa").mean()
