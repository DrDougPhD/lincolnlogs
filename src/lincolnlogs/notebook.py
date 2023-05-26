def called_me() -> bool:
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
       
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
       
        else:
            return False  # Other type (?)
 
    except NameError:
        return False      # Probably standard Python interpreter
   
    except ImportError:   # IPython is not installed, so this is not being called by a notebook
        return False
