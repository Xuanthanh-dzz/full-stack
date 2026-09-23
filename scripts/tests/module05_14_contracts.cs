using SpanSensorParser;
using System.Reflection;
internal static class Contracts
{
    private delegate bool Parser(ReadOnlySpan<char> text, out ReadingView reading);
    public static void Main()
    {
        var parser=typeof(SpanSensorParser.Program).GetMethod("TryParseReading",BindingFlags.NonPublic|BindingFlags.Static)!.CreateDelegate<Parser>();
        if(!parser("S,1,2,3,OK",out var valid)||valid.Sample1!=1||valid.Sample3!=3||!valid.SensorId.SequenceEqual("S"))throw new Exception("valid parser");
        foreach(var text in new[]{"", "S,1,2,OK", "S,1,2,3,OK,extra",",1,2,3,OK","S,NaN,2,3,OK","S,Infinity,2,3,OK","S,1e999,2,3,OK","S,1,2,3,BAD"})
            if(parser(text,out _))throw new Exception("accepted invalid: "+text);
        int[] values=[1,2,3];Span<int> view=values.AsSpan(1);view[0]=9;
        if(values[1]!=9)throw new Exception("slice alias");
    }
}
