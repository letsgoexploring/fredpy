
Additional ``fredpy`` Functions
==================================


.. py:function:: fredpy.divide(object1,object2)

            Divides the data from :py:data:`object1` by the data from :py:data:`object2`.

            :param object1: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object1: int,float,Numpy.ndarray, or similar or fredpy.series
            :param object2: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object2: int,float,Numpy.ndarray, or similar or fredpy.series
            :return: :py:class:`fredpy.series`
            
            
.. py:function:: fredpy.fred_api_request(api_key,path,parameters)

            Queries the FRED API. Returns a :py:class:`requests.models.Response` object if successful, otherwise will raise an error with a message that is hopefully helpful. Reference for API querries: https://fred.stlouisfed.org/docs/api/fred/

            :param str api_key: Your 32-character FRED API Key.
            :param str path: Path for FRED API.
            :param dict parameters: Dictionary containing appropriate parameters and values for the API query
            :return: :py:class:`requests.models.Response`

.. py:function:: fredpy.get_vintage_dates(series_id)

            Returns vintage dates for series available from ALFRED.

            :param str series_id: ID of FRED series.
            :return: :py:class:`list`


.. py:function:: fredpy.minus(object1,object2)

            Subtracts the data from :py:data:`object2` from the data from :py:data:`object1`.

            :param object1: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object1: int,float,Numpy.ndarray, or similar or fredpy.series
            :param object2: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object2: int,float,Numpy.ndarray, or similar or fredpy.series
            :return: :py:class:`fredpy.series`

.. py:function:: fredpy.plus(object1,object2)

            Adds the data from :py:data:`object1` to the data from :py:data:`object2`.

            :param object1: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object1: int,float,Numpy.ndarray, or similar or fredpy.series
            :param object2: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object2: int,float,Numpy.ndarray, or similar or fredpy.series
            :return: :py:class:`fredpy.series`

.. py:function:: fredpy.recessions(start=None,end=None,ax=None,color='0.5',alpha=0.5):

            Creates recession bars for time series plots.

            :param start: Starting date. Default: None
            :type start: str or Timestamp
            :param end: Ending date. Default: None
            :type end: str or Timestamp
            :param matplotlib.axes._subplots.AxesSubplot ax: Matplotlib axis object to plot recession bars. Default: None
            :param str color: Color of the bars. Default: '0.5'.
            :param float alpha: Transparency of the recession bars. Must be between 0 and 1. Default: 0.5.
            :return:

.. py:function:: fredpy.times(object1,object2)

            Multiplies the data from :py:data:`object1` with the data from :py:data:`object2`.

            :param object1: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object1: int,float,Numpy.ndarray, or similar or fredpy.series
            :param object2: A :py:class:`fredpy.series` object, number, array, or similar.
            :type object2: int,float,Numpy.ndarray, or similar or fredpy.series
            :return: :py:class:`fredpy.series`

.. py:function:: fredpy.toFredSeries(data,dates,frequency='',frequency_short='',last_updated='',notes='',release='',seasonal_adjustment='',seasonal_adjustment_short='',series_id='',source='',t=0,title='',units='',units_short='')

            Create a :py:class:`fredpy.series` from time series data not obtained from FRED.

            :param data: Data values.
            :type data: numpy.ndarray, Pandas.Series, or list
            :param dates: Array or list of dates. Elements formatted as either string (YYYY-MM-DD or MM-DD-YYYY) or :py:class:`pandas.tslib.Timestamp`.
            :type dates: list or numpy.ndarry
            :param str frequency: Observation frequency. Options: '', 'Daily', 'Weekly', 'Monthly', 'Quarterly', or 'Annual'. Default: empty string.
            :param str frequency_short: Observation frequency abbreviated. Options: '', 'D', 'W', 'M', 'Q', or 'A'. Default: empty string.
            :param str last_updated: Date data was last updated. Default: empty string.
            :param str notes: Default: empty string.
            :param str release: Notes about data. Default: empty string.
            :param str seasonal_adjustment: Default: empty string.
            :param str seasonal_adjustment_short: Default: empty string.
            :param str series_id: FRED series ID. Default: empty string.
            :param str source: Source of the data. Default: empty string.
            :param int t: Number of observations per year. Default: 0
            :param str title: Title of the data. Default: empty string.
            :param str units: Units of the data. Default: empty string.
            :param str units_short: Units of the data. Abbreviated. Default: empty string.
            :return: :py:class:`fredpy.series`

.. py:function:: fredpy.window_equalize(series_list)

	Adjusts the date windows for a collection of fredpy.series objects to the smallest common window.

	:param list series_list: A list of :py:class:`fredpy.series` objects
	:return: list of :py:class:`fredpy.series`