using MeasuredOptimization;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var flags=System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic;var type=typeof(MeasuredOptimization.Program);var a=type.GetMethod("BuildWithConcatenation",flags)!;var b=type.GetMethod("BuildWithStringBuilder",flags)!;foreach(var n in new[]{0,1,9,10,100,300}){var left=(string)a.Invoke(null,[n])!;var right=(string)b.Invoke(null,[n])!;string expected=string.Concat(Enumerable.Range(1,n).Select(x=>x.ToString(System.Globalization.CultureInfo.InvariantCulture)+","));Check(left==expected&&right==expected,"independent CSV oracle");}
}
}
