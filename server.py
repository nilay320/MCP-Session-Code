from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import os
import math
import cmath
import qrcode
import io
import base64
from dice_roller import DiceRoller

load_dotenv()

mcp = FastMCP("mcp-server")
client = TavilyClient(os.getenv("TAVILY_API_KEY"))

@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for information about the given query"""
    search_results = client.get_search_context(query=query)
    return search_results

@mcp.tool()
def roll_dice(notation: str, num_rolls: int = 1) -> str:
    """Roll the dice with the given notation"""
    roller = DiceRoller(notation, num_rolls)
    return str(roller)

@mcp.tool()
def scientific_calculator(expression: str) -> str:
    """
    Evaluate mathematical expressions using a scientific calculator.
    
    Supports:
    - Basic arithmetic: +, -, *, /, //, %, **
    - Scientific functions: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh
    - Logarithmic functions: log, log10, log2, ln (natural log)
    - Exponential functions: exp, sqrt, cbrt
    - Constants: pi, e, tau
    - Complex numbers: 1+2j, complex operations
    - Trigonometric functions work with radians by default
    - Use degrees(x) to convert radians to degrees, radians(x) to convert degrees to radians
    
    Examples:
    - "sin(pi/2)" -> 1.0
    - "log10(100)" -> 2.0
    - "sqrt(16)" -> 4.0
    - "2**3" -> 8
    - "exp(1)" -> 2.718281828459045
    """
    try:
        # Create a safe namespace with mathematical functions and constants
        safe_dict = {
            # Mathematical functions
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'atan2': math.atan2,
            'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
            'asinh': math.asinh, 'acosh': math.acosh, 'atanh': math.atanh,
            'log': math.log, 'log10': math.log10, 'log2': math.log2,
            'ln': math.log,  # Natural logarithm alias
            'exp': math.exp, 'sqrt': cmath.sqrt, 'cbrt': lambda x: x**(1/3),
            'pow': pow, 'abs': abs,
            'ceil': math.ceil, 'floor': math.floor, 'trunc': math.trunc,
            'round': round,
            'degrees': math.degrees, 'radians': math.radians,
            'factorial': math.factorial,
            'gcd': math.gcd, 'lcm': math.lcm if hasattr(math, 'lcm') else lambda a, b: abs(a*b) // math.gcd(a, b),
            
            # Constants
            'pi': math.pi, 'e': math.e, 'tau': math.tau,
            'inf': math.inf, 'nan': math.nan,
            
            # Complex number functions
            'complex': complex, 'real': lambda x: x.real if isinstance(x, complex) else x,
            'imag': lambda x: x.imag if isinstance(x, complex) else 0,
            'conjugate': lambda x: x.conjugate() if hasattr(x, 'conjugate') else x,
            'phase': cmath.phase, 'polar': cmath.polar, 'rect': cmath.rect,
            
            # Allow built-in mathematical operations
            '__builtins__': {}
        }
        
        # Replace common mathematical notation
        expression = expression.replace('^', '**')  # Allow ^ for exponentiation
        expression = expression.replace('mod', '%')  # Allow mod for modulo
        
        # Evaluate the expression
        result = eval(expression, safe_dict)
        
        # Format the result nicely
        if isinstance(result, complex):
            if abs(result.imag) < 1e-10:  # Essentially real
                real_part = result.real
                if abs(real_part) < 1e-10:
                    return "0"
                elif abs(real_part - round(real_part)) < 1e-10:
                    return str(int(round(real_part)))
                else:
                    return str(real_part)
            else:
                real_str = str(int(result.real)) if abs(result.real - round(result.real)) < 1e-10 else str(result.real)
                imag_str = str(int(result.imag)) if abs(result.imag - round(result.imag)) < 1e-10 else str(result.imag)
                
                if result.real == 0:
                    return f"{imag_str}j" if result.imag != 1 else "j" if result.imag == 1 else "-j"
                else:
                    if result.imag >= 0:
                        imag_part = f" + {imag_str}j" if result.imag != 1 else " + j"
                    else:
                        imag_part = f" - {abs(float(imag_str))}j" if result.imag != -1 else " - j"
                    return f"{real_str}{imag_part}"
        elif isinstance(result, float):
            # Round very small numbers to avoid floating point precision issues
            if abs(result) < 1e-10:
                return "0"
            elif abs(result - round(result)) < 1e-10:
                return str(int(round(result)))
            else:
                return str(result)
        else:
            return str(result)
            
    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Error: Invalid mathematical operation - {str(e)}"
    except OverflowError:
        return "Error: Result too large to compute"
    except TypeError as e:
        return f"Error: Invalid expression type - {str(e)}"
    except SyntaxError:
        return "Error: Invalid mathematical expression syntax"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def generate_qr_code(data: str, error_correction: str = "M", border: int = 4, box_size: int = 10) -> str:
    """
    Generate a QR code for the given data.
    
    Args:
        data: The text or URL to encode in the QR code
        error_correction: Error correction level - "L" (Low ~7%), "M" (Medium ~15%), "Q" (Quartile ~25%), "H" (High ~30%)
        border: Size of the border (minimum is 4)
        box_size: Size of each box in pixels (default 10)
    
    Returns:
        Base64 encoded PNG image of the QR code that can be displayed or saved
    """
    try:
        # Set error correction level
        error_levels = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M, 
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H
        }
        
        if error_correction not in error_levels:
            return f"Error: Invalid error correction level. Use L, M, Q, or H"
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Controls size (1 is smallest)
            error_correction=error_levels[error_correction],
            box_size=box_size,
            border=max(border, 4),  # Minimum border is 4
        )
        
        # Add data
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for easy transmission
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"QR code generated successfully for: '{data[:50]}{'...' if len(data) > 50 else ''}'\nBase64 PNG: data:image/png;base64,{img_str}"
        
    except Exception as e:
        return f"Error generating QR code: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")